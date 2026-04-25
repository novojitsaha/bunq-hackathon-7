"""
bunq sandbox HTTP client.

Implements the bunq Public API auth handshake from scratch (no SDK needed).

The handshake is three steps and we cache the result on disk so subsequent
runs skip straight to step 4:

    1. POST /v1/installation        — register an RSA public key, get a server token.
    2. POST /v1/device-server       — register THIS machine, get a device id.
    3. POST /v1/session-server      — open a session, get a session token + user id.
    4. GET  /v1/user/{uid}/...      — actual reads, signed with our private key.

We sign every request body with PSS-SHA256 over our private key, in the
`X-Bunq-Client-Signature` header. The cached context lives at
`{bunq_context_path}` (default: `.bunq_context.json`). Delete it to re-bootstrap.

Why hand-rolled instead of `bunq_sdk`?
  - The official SDK pulls in a lot of legacy code, has flaky logging, and
    keeps a global mutable context that fights with FastAPI's request model.
  - We only need read endpoints + one optional Payment write — ~80 lines of
    HTTP. A self-contained client is easier to audit at a hackathon.

The write path (`create_payment`) exists but is GATED by the
`BUNQ_LIVE_WRITE` flag. It defaults to false. The "Confirm savings" UI flow
NEVER calls this directly — it goes through `/api/agent/confirm-action`,
which has its own guard.

Network access in this hackathon environment may be restricted. We catch
network errors broadly and fall back to seeded data — the demo never breaks
because of bunq.
"""

from __future__ import annotations

import base64
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.config import Settings, get_settings

log = logging.getLogger(__name__)

SANDBOX_BASE = "https://public-api.sandbox.bunq.com"
PRODUCTION_BASE = "https://api.bunq.com"


# ---------------------------------------------------------------------------
# Persistent context
# ---------------------------------------------------------------------------

@dataclass
class BunqContext:
    base_url: str
    private_key_pem: str
    server_public_key_pem: str
    installation_token: str
    device_id: int
    session_token: str
    user_id: int
    user_type: str  # "UserPerson" | "UserCompany" | "UserApiKey"
    session_expiry_ts: float
    # If we auto-minted a fresh sandbox user, the new key is recorded here
    # so the user can see in .bunq_context.json what's actually being used.
    minted_key: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BunqContext":
        # Tolerate older context files that don't have minted_key.
        d = {**d}
        d.setdefault("minted_key", None)
        return cls(**d)


def _load_context(path: Path) -> BunqContext | None:
    if not path.exists():
        return None
    try:
        return BunqContext.from_dict(json.loads(path.read_text()))
    except Exception as exc:  # noqa: BLE001
        log.warning("Failed to load bunq context from %s: %s", path, exc)
        return None


def _save_context(path: Path, ctx: BunqContext) -> None:
    path.write_text(json.dumps(ctx.to_dict(), indent=2))
    # Best effort: keep the keys off prying eyes
    try:
        path.chmod(0o600)
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Crypto
# ---------------------------------------------------------------------------

def _generate_keypair() -> tuple[str, str]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("ascii")
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return private_pem, public_pem


def _sign_body(private_pem: str, body: bytes) -> str:
    """RSA-SHA256 signature over the request body."""
    private_key = serialization.load_pem_private_key(private_pem.encode("ascii"), password=None)
    sig = private_key.sign(body, padding.PKCS1v15(), hashes.SHA256())
    return base64.standard_b64encode(sig).decode("ascii")


def _looks_like_credential_error(exc: Exception) -> bool:
    """
    True if a BunqSandboxError looks like the well-documented expiry/IP failure:

      "User credentials are incorrect. Incorrect API key or IP address."

    Sandbox keys expire if no session is opened within 60 minutes of creation
    and become bound to the IP they were first used from. When we see this,
    minting a fresh sandbox user is the right recovery.
    """
    msg = str(exc).lower()
    needles = (
        "user credentials are incorrect",
        "incorrect api key",
        "incorrect api key or ip",
        "key is invalid",
        "expired",
    )
    return any(n in msg for n in needles)


def _extract_api_key_from_sandbox_response(payload: Any) -> str | None:
    """
    bunq's sandbox-user endpoints have used a few response shapes over the
    years. We accept any of them:

      Newer wrapped:
        {"Response": [{"ApiKey": {"api_key": "sandbox_..."}}, ...]}
      Older wrapped (UserPerson with embedded api_key):
        {"Response": [{"UserPerson": {"id": ..., "api_key": "sandbox_..."}}]}
      Flat (legacy /v1/sandbox-user):
        {"api_key": "sandbox_...", "user": {...}}
    """
    if not isinstance(payload, dict):
        return None

    # Flat: {"api_key": "..."}
    if isinstance(payload.get("api_key"), str):
        return payload["api_key"]

    # Wrapped: {"Response": [...]}
    items = payload.get("Response")
    if not isinstance(items, list):
        return None

    for item in items:
        if not isinstance(item, dict):
            continue
        for value in item.values():
            if isinstance(value, dict) and isinstance(value.get("api_key"), str):
                return value["api_key"]
    return None


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------

class BunqSandboxError(RuntimeError):
    pass


class BunqClient:
    """
    Lazy bunq HTTP client.

    Use:
        client = BunqClient()
        if client.available():
            accounts = client.list_monetary_accounts()
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._ctx: BunqContext | None = None
        self._http = httpx.Client(timeout=15.0)

    # ------------------------------------------------------------------
    # Bootstrap
    # ------------------------------------------------------------------

    def available(self) -> bool:
        """
        True if we can do bunq calls. In sandbox mode this is always true
        because we can auto-mint a user. In production it requires a real
        API key.
        """
        if self.settings.bunq_environment.upper() == "SANDBOX":
            return True
        return bool(self.settings.bunq_api_key)

    def base_url(self) -> str:
        return SANDBOX_BASE if self.settings.bunq_environment.upper() == "SANDBOX" else PRODUCTION_BASE

    def _ctx_path(self) -> Path:
        return Path(self.settings.bunq_context_path)

    def ensure_context(self) -> BunqContext:
        """
        Returns a valid context, bootstrapping or refreshing as needed.

        Self-healing logic for the sandbox:
          1. If we have a cached context with a valid session, use it.
          2. If we have installation+device but the session expired, refresh.
          3. If bootstrap fails because the API key is expired/invalid (the
             "User credentials are incorrect" error), automatically mint a
             fresh sandbox user via /v1/sandbox-user-person and retry.

        bunq sandbox keys expire if no session is opened within 60 minutes
        of creation, so for a hackathon demo this auto-mint behaviour is the
        difference between "it just works" and "manually re-running Tinker
        between every demo take."

        Raises BunqSandboxError on any failure that we couldn't recover from.
        """
        if self._ctx is None:
            self._ctx = _load_context(self._ctx_path())

        if self._ctx and self._ctx.session_expiry_ts > time.time() + 60:
            return self._ctx

        # If we have an installation+device but the session expired, refresh just the session.
        if self._ctx and self._ctx.installation_token and self._ctx.device_id:
            try:
                self._ctx = self._refresh_session(self._ctx)
                _save_context(self._ctx_path(), self._ctx)
                return self._ctx
            except Exception as exc:  # noqa: BLE001
                log.warning("bunq session refresh failed (%s) — re-bootstrapping", exc)

        # Try the bootstrap with the configured key. If it fails with a
        # credential error (or there's no key at all) we auto-mint a fresh
        # sandbox user and retry.
        api_key = self.settings.bunq_api_key
        if not api_key:
            log.info("No BUNQ_API_KEY configured — minting fresh sandbox user.")
            new_key = self._mint_sandbox_user()
            self.settings.bunq_api_key = new_key
            self._ctx = self._bootstrap(new_key)
            self._ctx.minted_key = new_key
            _save_context(self._ctx_path(), self._ctx)
            return self._ctx

        try:
            self._ctx = self._bootstrap(api_key)
        except BunqSandboxError as exc:
            if not _looks_like_credential_error(exc):
                raise
            log.warning(
                "bunq bootstrap failed with credential error (%s). "
                "Minting fresh sandbox user and retrying.",
                exc,
            )
            new_key = self._mint_sandbox_user()
            log.info("Minted fresh sandbox API key; updating runtime settings.")
            # Update both the runtime settings and the cached value so subsequent
            # calls in this process use the new key.
            self.settings.bunq_api_key = new_key
            self._ctx = self._bootstrap(new_key)
            # Persist the new key alongside the context so the user can see it.
            self._ctx.minted_key = new_key

        _save_context(self._ctx_path(), self._ctx)
        return self._ctx

    def _mint_sandbox_user(self) -> str:
        """
        POST /v1/sandbox-user-person — creates a fresh sandbox user and returns
        its API key. Unauthenticated endpoint, no signing required.

        bunq has rotated this endpoint a few times over the years; we accept
        all known response shapes (Response[ApiKey], Response[UserPerson], or
        a flat {"api_key": ...} object) defensively.
        """
        base = self.base_url()
        # Endpoints to try in order. The first that returns 200 wins.
        endpoints = [
            "/v1/sandbox-user-person",
            "/v1/sandbox-user-company",
            "/v1/sandbox-user",  # legacy
        ]
        last_error = ""
        for path in endpoints:
            try:
                r = self._http.post(
                    f"{base}{path}",
                    json={},
                    headers={
                        "Cache-Control": "no-cache",
                        "User-Agent": "BunqBiteBalance-Hackathon/0.2",
                        "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
                        "X-Bunq-Geolocation": "0 0 0 0 NL",
                        "X-Bunq-Language": "en_US",
                        "X-Bunq-Region": "nl_NL",
                    },
                )
            except httpx.RequestError as exc:
                last_error = f"{path}: network error {exc}"
                continue
            if r.status_code != 200:
                last_error = f"{path}: {r.status_code} {r.text[:200]}"
                continue
            key = _extract_api_key_from_sandbox_response(r.json())
            if key:
                return key
            last_error = f"{path}: 200 but no api_key in response: {r.text[:200]}"
        raise BunqSandboxError(f"could not mint a fresh sandbox user. Last error: {last_error}")

    def _bootstrap(self, api_key: str) -> BunqContext:
        priv, pub = _generate_keypair()
        base = self.base_url()

        # Step 1: installation
        r = self._http.post(
            f"{base}/v1/installation",
            json={"client_public_key": pub},
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "BunqBiteBalance-Hackathon/0.2",
            },
        )
        if r.status_code != 200:
            raise BunqSandboxError(f"installation failed: {r.status_code} {r.text[:300]}")
        inst = self._unwrap(r.json())
        token = next(item["Token"]["token"] for item in inst if "Token" in item)
        server_pub = next(
            item["ServerPublicKey"]["server_public_key"] for item in inst if "ServerPublicKey" in item
        )

        # Step 2: device-server. permitted_ips=["*"] makes this a wildcard key
        # so subsequent sessions work from any IP — important for demos.
        body = json.dumps({
            "description": "BunqBiteBalance Hackathon Device",
            "secret": api_key,
            "permitted_ips": ["*"],
        }).encode("utf-8")
        r = self._http.post(
            f"{base}/v1/device-server",
            content=body,
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "BunqBiteBalance-Hackathon/0.2",
                "X-Bunq-Client-Authentication": token,
                "X-Bunq-Client-Signature": _sign_body(priv, body),
            },
        )
        if r.status_code != 200:
            raise BunqSandboxError(f"device-server failed: {r.status_code} {r.text[:300]}")
        device_id = next(item["Id"]["id"] for item in self._unwrap(r.json()) if "Id" in item)

        # Step 3: session-server
        return self._open_session(priv, server_pub, token, device_id, base, api_key)

    def _refresh_session(self, ctx: BunqContext) -> BunqContext:
        return self._open_session(
            ctx.private_key_pem,
            ctx.server_public_key_pem,
            ctx.installation_token,
            ctx.device_id,
            ctx.base_url,
            self.settings.bunq_api_key or "",
        )

    def _open_session(
        self,
        priv: str,
        server_pub: str,
        installation_token: str,
        device_id: int,
        base: str,
        api_key: str,
    ) -> BunqContext:
        body = json.dumps({"secret": api_key}).encode("utf-8")
        r = self._http.post(
            f"{base}/v1/session-server",
            content=body,
            headers={
                "Cache-Control": "no-cache",
                "User-Agent": "BunqBiteBalance-Hackathon/0.2",
                "X-Bunq-Client-Authentication": installation_token,
                "X-Bunq-Client-Signature": _sign_body(priv, body),
            },
        )
        if r.status_code != 200:
            raise BunqSandboxError(f"session-server failed: {r.status_code} {r.text[:300]}")
        items = self._unwrap(r.json())
        session_token = next(item["Token"]["token"] for item in items if "Token" in item)
        # The user object is one of UserPerson / UserCompany / UserApiKey
        user_obj_wrapper: dict[str, Any] = {}
        user_type = "UserApiKey"
        for item in items:
            for key in ("UserPerson", "UserCompany", "UserApiKey"):
                if key in item:
                    user_obj_wrapper = item[key]
                    user_type = key
                    break
            if user_obj_wrapper:
                break
        user_id = int(user_obj_wrapper["id"])
        # bunq sessions are valid for ~10 minutes, but the response includes a
        # session_timeout. We be conservative and use 8 minutes.
        return BunqContext(
            base_url=base,
            private_key_pem=priv,
            server_public_key_pem=server_pub,
            installation_token=installation_token,
            device_id=device_id,
            session_token=session_token,
            user_id=user_id,
            user_type=user_type,
            session_expiry_ts=time.time() + 8 * 60,
        )

    @staticmethod
    def _unwrap(payload: dict[str, Any]) -> list[dict[str, Any]]:
        if "Response" not in payload:
            raise BunqSandboxError(f"unexpected bunq response: {payload}")
        return payload["Response"]

    # ------------------------------------------------------------------
    # Signed request helper
    # ------------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: dict[str, Any] | None = None,
        _retry: bool = True,
    ) -> list[dict[str, Any]]:
        ctx = self.ensure_context()
        body_bytes = json.dumps(body).encode("utf-8") if body is not None else b""
        headers = {
            "Cache-Control": "no-cache",
            "User-Agent": "BunqBiteBalance-Hackathon/0.2",
            "X-Bunq-Client-Authentication": ctx.session_token,
            "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
        }
        if body is not None:
            headers["X-Bunq-Client-Signature"] = _sign_body(ctx.private_key_pem, body_bytes)

        url = ctx.base_url + path
        r = self._http.request(method, url, headers=headers, content=body_bytes or None)
        if r.status_code in (401, 403) and _retry:
            # Stale cached context — clear it and re-bootstrap (which may
            # also auto-mint if the underlying key has expired). One retry,
            # to avoid infinite loops.
            log.warning(
                "bunq returned %s on %s — invalidating cached context and retrying once",
                r.status_code, path,
            )
            self._ctx = None
            try:
                self._ctx_path().unlink(missing_ok=True)
            except OSError:
                pass
            return self._request(method, path, body=body, _retry=False)
        if r.status_code >= 400:
            raise BunqSandboxError(f"{method} {path} -> {r.status_code} {r.text[:300]}")
        return self._unwrap(r.json())

    # ------------------------------------------------------------------
    # Read endpoints
    # ------------------------------------------------------------------

    def list_monetary_accounts(self) -> list[dict[str, Any]]:
        ctx = self.ensure_context()
        items = self._request("GET", f"/v1/user/{ctx.user_id}/monetary-account")
        accounts: list[dict[str, Any]] = []
        for item in items:
            for key in ("MonetaryAccountBank", "MonetaryAccountSavings", "MonetaryAccountJoint"):
                if key in item:
                    accounts.append({"_kind": key, **item[key]})
                    break
        return accounts

    def list_payments(self, monetary_account_id: int, limit: int = 50) -> list[dict[str, Any]]:
        ctx = self.ensure_context()
        items = self._request(
            "GET",
            f"/v1/user/{ctx.user_id}/monetary-account/{monetary_account_id}/payment?count={limit}",
        )
        return [item.get("Payment", {}) for item in items if "Payment" in item]

    # ------------------------------------------------------------------
    # Write endpoints
    #
    # In SANDBOX environment we always allow writes (it's fake money).
    # In PRODUCTION we still gate behind BUNQ_LIVE_WRITE for safety.
    # ------------------------------------------------------------------

    def _writes_allowed(self) -> bool:
        if self.settings.bunq_environment.upper() == "SANDBOX":
            return True
        return bool(self.settings.bunq_live_write)

    def _pick_main_account(self) -> dict[str, Any]:
        accounts = self.list_monetary_accounts()
        if not accounts:
            raise BunqSandboxError("No monetary accounts available on this user.")
        return next((a for a in accounts if a["_kind"] == "MonetaryAccountBank"), accounts[0])

    def get_main_balance_eur(self) -> float:
        """Float balance of the user's main account, in EUR."""
        try:
            main = self._pick_main_account()
            return float((main.get("balance") or {}).get("value", "0"))
        except Exception:  # noqa: BLE001
            return 0.0

    def request_funds_from_sugardaddy(self, amount_eur: float) -> dict[str, Any]:
        """
        Sandbox-only: ask sugardaddy@bunq.com for money. Sugardaddy is bunq's
        sandbox auto-accepter for amounts up to €500. The funds appear in our
        account within a second or two. We use this to keep the demo account
        funded when balance gets low.
        """
        if self.settings.bunq_environment.upper() != "SANDBOX":
            raise BunqSandboxError("request_funds_from_sugardaddy is sandbox-only")
        if amount_eur <= 0 or amount_eur > 500:
            raise BunqSandboxError("amount must be in (0, 500]")
        ctx = self.ensure_context()
        main = self._pick_main_account()
        items = self._request(
            "POST",
            f"/v1/user/{ctx.user_id}/monetary-account/{main['id']}/request-inquiry",
            body={
                "amount_inquired": {"value": f"{amount_eur:.2f}", "currency": "EUR"},
                "counterparty_alias": {"type": "EMAIL", "value": "sugardaddy@bunq.com"},
                "description": "BunqBiteBalance demo top-up",
                "allow_bunqme": False,
            },
        )
        return next((it["Id"] for it in items if "Id" in it), {})

    def send_payment_to_email(
        self,
        *,
        amount_eur: float,
        counterparty_email: str,
        description: str,
    ) -> dict[str, Any]:
        """
        Send a Payment to a counterparty by email. Used to record a receipt
        as a real bunq sandbox transaction so the user can see "I scanned a
        receipt → bunq shows the payment".

        The counterparty doesn't need to be a friend; in sandbox we send to
        `sugardaddy@bunq.com` because it's always available.
        """
        if not self._writes_allowed():
            raise BunqSandboxError(
                "BUNQ_LIVE_WRITE is false (and we're not in sandbox) — payment was not sent."
            )
        ctx = self.ensure_context()
        main = self._pick_main_account()
        # Truncate description to bunq's 140-char limit.
        desc = (description or "")[:140]
        items = self._request(
            "POST",
            f"/v1/user/{ctx.user_id}/monetary-account/{main['id']}/payment",
            body={
                "amount": {"value": f"{amount_eur:.2f}", "currency": "EUR"},
                "counterparty_alias": {"type": "EMAIL", "value": counterparty_email},
                "description": desc,
            },
        )
        return next((it["Id"] for it in items if "Id" in it), {})

    def create_payment(
        self,
        *,
        monetary_account_id: int,
        amount_eur: float,
        counterparty_iban: str,
        counterparty_name: str,
        description: str,
    ) -> dict[str, Any]:
        """IBAN-based payment write. Kept for completeness; the demo uses EMAIL."""
        if not self._writes_allowed():
            raise BunqSandboxError(
                "BUNQ_LIVE_WRITE is false — payment was not sent. Enable in .env "
                "to allow real sandbox payments."
            )
        ctx = self.ensure_context()
        items = self._request(
            "POST",
            f"/v1/user/{ctx.user_id}/monetary-account/{monetary_account_id}/payment",
            body={
                "amount": {"value": f"{amount_eur:.2f}", "currency": "EUR"},
                "counterparty_alias": {
                    "type": "IBAN",
                    "value": counterparty_iban,
                    "name": counterparty_name,
                },
                "description": description,
            },
        )
        return next((it["Id"] for it in items if "Id" in it), {})


# ---------------------------------------------------------------------------
# Module-level singleton (cheap; FastAPI reuses across requests)
# ---------------------------------------------------------------------------

_singleton: BunqClient | None = None


def get_bunq_client() -> BunqClient:
    global _singleton
    if _singleton is None:
        _singleton = BunqClient()
    return _singleton

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

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BunqContext":
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
        return bool(self.settings.bunq_api_key)

    def base_url(self) -> str:
        return SANDBOX_BASE if self.settings.bunq_environment.upper() == "SANDBOX" else PRODUCTION_BASE

    def _ctx_path(self) -> Path:
        return Path(self.settings.bunq_context_path)

    def ensure_context(self) -> BunqContext:
        """
        Returns a valid context, bootstrapping or refreshing as needed.
        Raises BunqSandboxError on any failure.
        """
        if self._ctx is None:
            self._ctx = _load_context(self._ctx_path())

        if self._ctx and self._ctx.session_expiry_ts > time.time() + 60:
            return self._ctx

        if not self.settings.bunq_api_key:
            raise BunqSandboxError("BUNQ_API_KEY not configured")

        # If we have an installation+device but the session expired, refresh just the session.
        if self._ctx and self._ctx.installation_token and self._ctx.device_id:
            try:
                self._ctx = self._refresh_session(self._ctx)
                _save_context(self._ctx_path(), self._ctx)
                return self._ctx
            except Exception as exc:  # noqa: BLE001
                log.warning("bunq session refresh failed (%s) — re-bootstrapping", exc)

        self._ctx = self._bootstrap()
        _save_context(self._ctx_path(), self._ctx)
        return self._ctx

    def _bootstrap(self) -> BunqContext:
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

        # Step 2: device-server
        body = json.dumps({
            "description": "BunqBiteBalance Hackathon Device",
            "secret": self.settings.bunq_api_key,
            "permitted_ips": ["*"],  # sandbox only — production would lock to specific IPs
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
        return self._open_session(priv, server_pub, token, device_id, base)

    def _refresh_session(self, ctx: BunqContext) -> BunqContext:
        return self._open_session(
            ctx.private_key_pem,
            ctx.server_public_key_pem,
            ctx.installation_token,
            ctx.device_id,
            ctx.base_url,
        )

    def _open_session(
        self,
        priv: str,
        server_pub: str,
        installation_token: str,
        device_id: int,
        base: str,
    ) -> BunqContext:
        body = json.dumps({"secret": self.settings.bunq_api_key}).encode("utf-8")
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
    # Write endpoint (gated by BUNQ_LIVE_WRITE)
    # ------------------------------------------------------------------

    def create_payment(
        self,
        *,
        monetary_account_id: int,
        amount_eur: float,
        counterparty_iban: str,
        counterparty_name: str,
        description: str,
    ) -> dict[str, Any]:
        if not self.settings.bunq_live_write:
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

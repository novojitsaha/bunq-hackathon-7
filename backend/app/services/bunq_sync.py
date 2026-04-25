"""
Pulls bunq sandbox payments into the local Transaction table.

Modes:
  - "demo":  no BUNQ_API_KEY set, or live call failed.
             Seeds deterministic demo transactions so the dashboard is populated.
  - "live":  BUNQ_API_KEY set and the handshake + read succeeded.
             We pull real payments from the user's first monetary account and
             upsert them into the DB (idempotent on bunq_payment_id).

The demo path is the safe default. The live path is authoritative when
available — judges who provide a sandbox key see real bunq data flowing in.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Any

from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.models import MerchantCategory, Transaction, TransactionDirection
from app.services.bunq_client import BunqClient, BunqSandboxError, get_bunq_client
from app.services.demo_data import DEMO_TRANSACTIONS
from app.services.transaction_matcher import classify_merchant

log = logging.getLogger(__name__)


def sync_transactions(session: Session, settings: Settings | None = None) -> tuple[str, int, str]:
    settings = settings or get_settings()
    if not settings.bunq_api_key:
        created = seed_demo_transactions(session)
        return "demo", created, "No BUNQ_API_KEY configured; seeded demo transactions."

    try:
        client = get_bunq_client()
        accounts = client.list_monetary_accounts()
        if not accounts:
            created = seed_demo_transactions(session)
            return "demo", created, "bunq returned no monetary accounts; seeded demo transactions."

        # Use the first non-savings account as the "main" account.
        main = next((a for a in accounts if a["_kind"] == "MonetaryAccountBank"), accounts[0])
        payments = client.list_payments(int(main["id"]), limit=50)
    except BunqSandboxError as exc:
        log.warning("bunq sync failed: %s — seeding demo data", exc)
        created = seed_demo_transactions(session)
        return "demo", created, f"bunq sync failed ({type(exc).__name__}); seeded demo transactions."

    created = 0
    for payment in payments:
        if _upsert_payment(session, payment):
            created += 1
    session.commit()
    return "live", created, f"Pulled {len(payments)} payments from bunq sandbox; {created} new."


def seed_demo_transactions(session: Session) -> int:
    created = 0
    for transaction_data in DEMO_TRANSACTIONS:
        existing = session.exec(
            select(Transaction).where(Transaction.bunq_payment_id == transaction_data["bunq_payment_id"])
        ).first()
        if existing:
            continue
        is_food, confidence, category = classify_merchant(
            transaction_data["merchant_name"], transaction_data.get("description")
        )
        session.add(
            Transaction(
                **transaction_data,
                is_food_candidate=is_food,
                food_confidence=confidence,
                merchant_category=category,
            )
        )
        created += 1
    session.commit()
    return created


# ---------------------------------------------------------------------------
# Webhook payload upsert
# ---------------------------------------------------------------------------

def upsert_webhook_payment(session: Session, payload: dict) -> Transaction | None:
    payment = payload.get("Payment") or payload.get("payment") or payload
    return _upsert_payment_obj(session, payment, commit=True)


def _upsert_payment(session: Session, payment: dict[str, Any]) -> bool:
    """Upsert a Payment object pulled from the bunq REST API. Returns True if new."""
    return _upsert_payment_obj(session, payment, commit=False) is not None


def _upsert_payment_obj(
    session: Session, payment: dict[str, Any], *, commit: bool
) -> Transaction | None:
    payment_id = str(payment.get("id") or payment.get("bunq_payment_id") or "")
    if not payment_id:
        return None

    existing = session.exec(
        select(Transaction).where(Transaction.bunq_payment_id == payment_id)
    ).first()
    if existing:
        return None

    amount_payload = payment.get("amount") or {}
    try:
        amount = float(amount_payload.get("value", payment.get("amount_value", 0)) or 0)
    except (TypeError, ValueError):
        amount = 0.0

    merchant = (
        ((payment.get("counterparty_alias") or {}).get("display_name"))
        or ((payment.get("counterparty_alias") or {}).get("label_user", {}) or {}).get("display_name")
        or payment.get("merchant_name")
        or payment.get("description")
        or "bunq payment"
    )
    description = payment.get("description")

    payment_date_str = payment.get("created") or payment.get("payment_date")
    try:
        payment_date = (
            datetime.fromisoformat(payment_date_str.replace("Z", "+00:00"))
            if payment_date_str else datetime.now(UTC)
        )
    except (AttributeError, ValueError):
        payment_date = datetime.now(UTC)

    direction = TransactionDirection.OUTGOING if amount < 0 else TransactionDirection.INCOMING
    is_food, confidence, category = classify_merchant(merchant, description)

    transaction = Transaction(
        bunq_payment_id=payment_id,
        merchant_name=merchant,
        description=description,
        amount=amount,
        payment_date=payment_date,
        direction=direction,
        is_food_candidate=is_food,
        food_confidence=confidence,
        merchant_category=category,
    )
    session.add(transaction)
    if commit:
        session.commit()
        session.refresh(transaction)
    return transaction

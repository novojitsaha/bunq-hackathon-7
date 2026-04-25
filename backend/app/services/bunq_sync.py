from sqlmodel import Session, select

from app.config import Settings, get_settings
from app.models import Transaction
from app.services.demo_data import DEMO_TRANSACTIONS
from app.services.transaction_matcher import classify_merchant


def sync_transactions(session: Session, settings: Settings | None = None) -> tuple[str, int, str]:
    settings = settings or get_settings()
    if not settings.bunq_api_key:
        created = seed_demo_transactions(session)
        return "demo", created, "No BUNQ_API_KEY configured; seeded demo transactions."
    return (
        "live-placeholder",
        0,
        "BUNQ_API_KEY is configured. Toolkit adapter boundary is present; live sync can be wired here.",
    )


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


def upsert_webhook_payment(session: Session, payload: dict) -> Transaction | None:
    payment = payload.get("Payment") or payload.get("payment") or payload
    payment_id = str(payment.get("id") or payment.get("bunq_payment_id") or "")
    if not payment_id:
        return None
    existing = session.exec(select(Transaction).where(Transaction.bunq_payment_id == payment_id)).first()
    if existing:
        return existing

    amount_payload = payment.get("amount") or {}
    amount = float(amount_payload.get("value", payment.get("amount_value", 0)) or 0)
    merchant = (
        ((payment.get("counterparty_alias") or {}).get("display_name"))
        or payment.get("merchant_name")
        or payment.get("description")
        or "bunq payment"
    )
    description = payment.get("description")
    is_food, confidence, category = classify_merchant(merchant, description)
    transaction = Transaction(
        bunq_payment_id=payment_id,
        merchant_name=merchant,
        description=description,
        amount=amount,
        is_food_candidate=is_food,
        food_confidence=confidence,
        merchant_category=category,
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


from datetime import datetime

from sqlmodel import Session, select

from app.models import ProductMatch, Receipt, ReceiptItem, ReceiptStatus, Transaction, utc_now
from app.services.ai_receipt_extractor import ExtractedReceipt, ReceiptExtractor
from app.services.nutrition_lookup import enrich_item, normalize_item_name
from app.services.transaction_matcher import receipt_transaction_score


def _parse_purchase_date(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


async def create_receipt_from_upload(
    session: Session, *, filename: str | None, content_type: str | None, content: bytes
) -> Receipt:
    receipt = Receipt(upload_filename=filename, file_type=content_type, status=ReceiptStatus.PROCESSING)
    session.add(receipt)
    session.commit()
    session.refresh(receipt)

    extractor = ReceiptExtractor()
    extracted, raw = await extractor.extract(filename=filename, content_type=content_type, content=content)
    await apply_extraction(session, receipt, extracted, raw)
    return receipt


async def apply_extraction(session: Session, receipt: Receipt, extracted: ExtractedReceipt, raw: str) -> None:
    receipt.merchant_name = extracted.merchant_name
    receipt.purchase_date = _parse_purchase_date(extracted.purchase_date)
    receipt.total_amount = extracted.total_amount
    receipt.currency = extracted.currency
    receipt.raw_extraction_json = raw
    receipt.validation_notes = "; ".join(extracted.warnings) if extracted.warnings else None
    receipt.status = ReceiptStatus.READY
    receipt.updated_at = utc_now()
    session.add(receipt)
    session.commit()
    session.refresh(receipt)

    for extracted_item in extracted.items:
        normalized = extracted_item.normalized_name or normalize_item_name(extracted_item.raw_name)
        enrichment = await enrich_item(extracted_item.raw_name, normalized)
        item = ReceiptItem(
            receipt_id=receipt.id or 0,
            raw_name=extracted_item.raw_name,
            normalized_name=enrichment["normalized_name"],
            quantity=extracted_item.quantity,
            unit=extracted_item.unit,
            total_price=extracted_item.total_price,
            calories_total=enrichment["calories_total"],
            classification=enrichment["classification"],
            confidence=enrichment["confidence"],
            source=enrichment["source"],
            selected_for_user=bool(enrichment["is_food"]),
            is_food=bool(enrichment["is_food"]),
        )
        session.add(item)
        session.commit()
        session.refresh(item)

        match = enrichment.get("match")
        if match is not None:
            session.add(
                ProductMatch(
                    item_id=item.id or 0,
                    normalized_query=item.normalized_name,
                    source=match.source,
                    external_id=match.external_id,
                    product_name=match.product_name,
                    brand=match.brand,
                    calories_per_100g=match.calories_per_100g,
                    serving_size=match.serving_size,
                    confidence=match.confidence,
                    raw_json=match.raw_json,
                )
            )
            session.commit()


def confirm_receipt(session: Session, receipt: Receipt) -> Receipt:
    receipt.status = ReceiptStatus.CONFIRMED
    receipt.updated_at = utc_now()

    # 1. Try the existing matching path first — if the user has a bunq
    #    transaction that already corresponds to this receipt (e.g. they
    #    actually paid with bunq), link them.
    transaction = best_transaction_match(session, receipt)

    # 2. If no match, create a real bunq sandbox payment so the receipt
    #    actually shows up in the bunq account. This is the important
    #    fix for the "I scanned a receipt but bunq doesn't see it" case.
    if transaction is None and receipt.total_amount and receipt.total_amount > 0:
        transaction = _record_receipt_as_bunq_payment(session, receipt)

    if transaction and transaction.id:
        receipt.linked_transaction_id = transaction.id
        transaction.matched_receipt_id = receipt.id
        session.add(transaction)

    session.add(receipt)
    session.commit()
    session.refresh(receipt)
    return receipt


def _record_receipt_as_bunq_payment(session: Session, receipt: Receipt) -> Transaction | None:
    """
    Send a real bunq sandbox Payment for this receipt's total to
    sugardaddy@bunq.com so it appears in the user's bunq account, then mirror
    it as a local Transaction record.

    Falls back gracefully (returns None) if bunq is unreachable, the account
    is unfunded, or any other error occurs — the receipt still confirms,
    we just don't get a bunq transaction for it.
    """
    from app.config import get_settings
    from app.models import MerchantCategory, TransactionDirection
    from app.services.bunq_client import BunqSandboxError, get_bunq_client
    from app.services.transaction_matcher import classify_merchant
    import logging

    log = logging.getLogger(__name__)
    settings = get_settings()
    if settings.bunq_environment.upper() != "SANDBOX" and not settings.bunq_live_write:
        log.info("Skipping bunq write for receipt #%s (live writes disabled).", receipt.id)
        return None

    description = f"{receipt.merchant_name or 'Receipt'} #{receipt.id}"
    try:
        client = get_bunq_client()
        # Make sure the account has funds for this payment.
        if client.get_main_balance_eur() < (receipt.total_amount or 0) + 1:
            try:
                client.request_funds_from_sugardaddy(500.0)
            except BunqSandboxError as exc:
                log.warning("Sandbox top-up before receipt payment failed: %s", exc)

        result = client.send_payment_to_email(
            amount_eur=float(receipt.total_amount or 0),
            counterparty_email="sugardaddy@bunq.com",
            description=description,
        )
    except BunqSandboxError as exc:
        log.warning("bunq write for receipt #%s failed: %s", receipt.id, exc)
        return None

    payment_id = str(result.get("id") or "")
    if not payment_id:
        log.warning("bunq payment for receipt #%s returned no id", receipt.id)
        return None

    is_food, confidence, category = classify_merchant(
        receipt.merchant_name or "", description
    )
    transaction = Transaction(
        bunq_payment_id=payment_id,
        merchant_name=receipt.merchant_name or "Receipt",
        description=description,
        amount=-float(receipt.total_amount or 0),
        currency=receipt.currency or "EUR",
        payment_date=receipt.purchase_date or utc_now(),
        direction=TransactionDirection.OUTGOING,
        is_food_candidate=is_food,
        food_confidence=max(confidence, 0.85),
        merchant_category=category if category != MerchantCategory.UNKNOWN else MerchantCategory.SUPERMARKET,
    )
    session.add(transaction)
    session.commit()
    session.refresh(transaction)
    return transaction


def best_transaction_match(session: Session, receipt: Receipt) -> Transaction | None:
    candidates = session.exec(
        select(Transaction)
        .where(Transaction.direction == "OUTGOING")
        .where(Transaction.matched_receipt_id.is_(None))
        .where(Transaction.is_food_candidate == True)  # noqa: E712
    ).all()
    best: tuple[float, Transaction | None] = (0.0, None)
    for transaction in candidates:
        score = receipt_transaction_score(
            receipt_total=receipt.total_amount,
            receipt_date=receipt.purchase_date,
            receipt_merchant=receipt.merchant_name,
            transaction_amount=transaction.amount,
            transaction_date=transaction.payment_date,
            transaction_merchant=transaction.merchant_name,
        )
        if score > best[0]:
            best = (score, transaction)
    return best[1] if best[0] >= 0.80 else None


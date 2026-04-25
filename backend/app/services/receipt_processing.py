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
    transaction = best_transaction_match(session, receipt)
    if transaction and transaction.id:
        receipt.linked_transaction_id = transaction.id
        transaction.matched_receipt_id = receipt.id
        session.add(transaction)
    session.add(receipt)
    session.commit()
    session.refresh(receipt)
    return receipt


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


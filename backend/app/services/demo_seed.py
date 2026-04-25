from sqlmodel import Session, delete, select

from app.models import Goal, ProductMatch, Receipt, ReceiptItem, ReceiptStatus, Transaction
from app.services.ai_receipt_extractor import ExtractedReceipt
from app.services.demo_data import DEMO_TRANSACTIONS, RECEIPT_FIXTURES
from app.services.receipt_processing import apply_extraction
from app.services.transaction_matcher import classify_merchant


def reset_demo(session: Session) -> None:
    for model in [ProductMatch, ReceiptItem, Receipt, Transaction, Goal]:
        session.exec(delete(model))
    session.commit()


async def seed_demo(session: Session) -> dict[str, int]:
    reset_demo(session)
    created_transactions = 0
    for transaction_data in DEMO_TRANSACTIONS:
        is_food, confidence, category = classify_merchant(
            transaction_data["merchant_name"], transaction_data.get("description")
        )
        transaction = Transaction(
            **transaction_data,
            is_food_candidate=is_food,
            food_confidence=confidence,
            merchant_category=category,
        )
        session.add(transaction)
        created_transactions += 1
    session.commit()

    created_receipts = 0
    for key in ["junk", "fast_food"]:
        fixture = ExtractedReceipt.model_validate(RECEIPT_FIXTURES[key])
        receipt = Receipt(
            upload_filename=f"{key}.jpg",
            file_type="image/jpeg",
            status=ReceiptStatus.PROCESSING,
        )
        session.add(receipt)
        session.commit()
        session.refresh(receipt)
        await apply_extraction(session, receipt, fixture, fixture.model_dump_json())
        receipt.status = ReceiptStatus.CONFIRMED
        session.add(receipt)
        session.commit()
        created_receipts += 1

    return {"receipts": created_receipts, "transactions": created_transactions}


def has_demo_data(session: Session) -> bool:
    return session.exec(select(Receipt)).first() is not None or session.exec(select(Transaction)).first() is not None


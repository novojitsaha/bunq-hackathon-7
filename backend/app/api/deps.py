from fastapi import HTTPException
from sqlmodel import Session, select

from app.models import Receipt, ReceiptItem, Transaction


def get_receipt_or_404(session: Session, receipt_id: int) -> Receipt:
    receipt = session.get(Receipt, receipt_id)
    if receipt is None:
        raise HTTPException(status_code=404, detail="Receipt not found")
    return receipt


def get_item_or_404(session: Session, item_id: int, receipt_id: int | None = None) -> ReceiptItem:
    item = session.get(ReceiptItem, item_id)
    if item is None or (receipt_id is not None and item.receipt_id != receipt_id):
        raise HTTPException(status_code=404, detail="Receipt item not found")
    return item


def receipt_with_items(session: Session, receipt: Receipt):
    from app.schemas import ReceiptItemRead, ReceiptRead

    items = session.exec(select(ReceiptItem).where(ReceiptItem.receipt_id == receipt.id)).all()
    return ReceiptRead.model_validate(receipt).model_copy(
        update={"items": [ReceiptItemRead.model_validate(item) for item in items]}
    )


def transaction_for_receipt(session: Session, transaction_id: int | None) -> Transaction | None:
    if transaction_id is None:
        return None
    return session.get(Transaction, transaction_id)


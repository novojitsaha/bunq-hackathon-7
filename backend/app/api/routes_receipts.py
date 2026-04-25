from fastapi import APIRouter, Depends, UploadFile
from sqlmodel import Session, select

from app.api.deps import get_item_or_404, get_receipt_or_404, receipt_with_items, transaction_for_receipt
from app.db import get_session
from app.models import ReceiptItem, utc_now
from app.schemas import ReceiptItemRead, ReceiptItemUpdate, ReceiptRead, ReceiptSummary, TransactionRead
from app.services.metrics import receipt_splits
from app.services.receipt_processing import confirm_receipt, create_receipt_from_upload

router = APIRouter(prefix="/api/receipts", tags=["receipts"])


@router.post("/upload", response_model=ReceiptRead)
async def upload_receipt(file: UploadFile, session: Session = Depends(get_session)):
    content = await file.read()
    receipt = await create_receipt_from_upload(
        session, filename=file.filename, content_type=file.content_type, content=content
    )
    return receipt_with_items(session, receipt)


@router.get("/{receipt_id}", response_model=ReceiptRead)
def get_receipt(receipt_id: int, session: Session = Depends(get_session)):
    receipt = get_receipt_or_404(session, receipt_id)
    return receipt_with_items(session, receipt)


@router.patch("/{receipt_id}/items/{item_id}", response_model=ReceiptItemRead)
def update_receipt_item(
    receipt_id: int, item_id: int, payload: ReceiptItemUpdate, session: Session = Depends(get_session)
):
    item = get_item_or_404(session, item_id, receipt_id)
    updates = payload.model_dump(exclude_unset=True)
    for field, value in updates.items():
        setattr(item, field, value)
    if payload.classification is not None and payload.classification.value == "NON_FOOD":
        item.is_food = False
        item.selected_for_user = False
    item.user_override = True
    item.updated_at = utc_now()
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@router.post("/{receipt_id}/confirm", response_model=ReceiptSummary)
def confirm(receipt_id: int, session: Session = Depends(get_session)):
    receipt = confirm_receipt(session, get_receipt_or_404(session, receipt_id))
    return build_summary(session, receipt.id or receipt_id)


@router.get("/{receipt_id}/summary", response_model=ReceiptSummary)
def summary(receipt_id: int, session: Session = Depends(get_session)):
    get_receipt_or_404(session, receipt_id)
    return build_summary(session, receipt_id)


def build_summary(session: Session, receipt_id: int) -> ReceiptSummary:
    receipt = get_receipt_or_404(session, receipt_id)
    calorie_split, spend_split = receipt_splits(session, receipt_id)
    items = session.exec(
        select(ReceiptItem)
        .where(ReceiptItem.receipt_id == receipt_id)
        .where(ReceiptItem.selected_for_user == True)  # noqa: E712
        .where(ReceiptItem.is_food == True)  # noqa: E712
    ).all()
    top_outside = sorted(
        [item for item in items if item.classification in {"DAGKEUZE", "WEEKKEUZE"}],
        key=lambda item: item.calories_total or 0,
        reverse=True,
    )[:5]
    transaction = transaction_for_receipt(session, receipt.linked_transaction_id)
    return ReceiptSummary(
        receipt_id=receipt_id,
        merchant_name=receipt.merchant_name,
        purchase_date=receipt.purchase_date,
        total_amount=receipt.total_amount,
        selected_spend=spend_split.total,
        selected_calories=calorie_split.total,
        spend_split=spend_split,
        calorie_split=calorie_split,
        top_outside_items=[ReceiptItemRead.model_validate(item) for item in top_outside],
        linked_transaction=TransactionRead.model_validate(transaction) if transaction else None,
    )


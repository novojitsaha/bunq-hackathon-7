from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import BunqSyncResponse, TransactionRead
from app.services.bunq_sync import sync_transactions, upsert_webhook_payment

router = APIRouter(prefix="/api/bunq", tags=["bunq"])


@router.post("/sync", response_model=BunqSyncResponse)
def sync_bunq(session: Session = Depends(get_session)):
    mode, created, message = sync_transactions(session)
    return BunqSyncResponse(mode=mode, created_transactions=created, message=message)


@router.post("/webhook", response_model=TransactionRead | dict)
def bunq_webhook(payload: dict, session: Session = Depends(get_session)):
    transaction = upsert_webhook_payment(session, payload)
    if transaction is None:
        return {"ok": True, "message": "Webhook received but no payment object was present."}
    return transaction


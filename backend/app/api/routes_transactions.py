from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app.db import get_session
from app.models import Transaction
from app.schemas import TransactionRead

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.get("", response_model=list[TransactionRead])
def list_transactions(session: Session = Depends(get_session)):
    return list(session.exec(select(Transaction).order_by(Transaction.payment_date.desc())).all())


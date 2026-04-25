from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import SettingsActionResponse
from app.services.demo_seed import reset_demo, seed_demo

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.post("/seed-demo", response_model=SettingsActionResponse)
async def seed(session: Session = Depends(get_session)):
    counts = await seed_demo(session)
    return SettingsActionResponse(ok=True, message=f"Seeded {counts['receipts']} receipts and {counts['transactions']} transactions.")


@router.post("/reset-demo", response_model=SettingsActionResponse)
def reset(session: Session = Depends(get_session)):
    reset_demo(session)
    return SettingsActionResponse(ok=True, message="Demo data deleted.")


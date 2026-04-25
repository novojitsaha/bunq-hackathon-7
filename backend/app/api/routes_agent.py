"""
Routes for the AI advisor agent.

  POST /api/agent/advise          — run the agent, return a plan + proposed actions
  POST /api/agent/confirm-action  — execute a proposed action after user click

The split is deliberate: Claude decides the strategy (advise), the user
authorises any side effect (confirm-action). For a hackathon demo with
BUNQ_LIVE_WRITE=false, the savings-transfer action records a Transaction
locally rather than firing a real bunq Payment — this is safe and the
demo story is identical from the audience's perspective.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException
from sqlmodel import Session

from app.config import get_settings
from app.db import get_session
from app.models import MerchantCategory, Transaction, TransactionDirection, utc_now
from app.services.ai_agent import AdvisorAgent

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/advise")
async def advise(session: Session = Depends(get_session)) -> dict[str, Any]:
    agent = AdvisorAgent()
    plan = await agent.advise(session)
    return plan.to_dict()


@router.post("/confirm-action")
def confirm_action(
    payload: dict[str, Any] = Body(...),
    session: Session = Depends(get_session),
) -> dict[str, Any]:
    kind = payload.get("kind")
    action_payload = payload.get("payload") or {}
    if kind != "savings_transfer":
        raise HTTPException(status_code=400, detail=f"Unknown action kind: {kind!r}")

    amount = float(action_payload.get("amount_eur", 0))
    if amount <= 0 or amount > 200:
        raise HTTPException(status_code=400, detail="amount_eur must be in (0, 200]")

    settings = get_settings()
    bunq_id_prefix = "schijf-buffer"

    if settings.bunq_live_write and settings.bunq_api_key:
        # Real bunq path. We deliberately do NOT execute it in the demo.
        # Wire up `bunq_client.py:create_payment(...)` here when ready.
        raise HTTPException(
            status_code=501,
            detail=(
                "BUNQ_LIVE_WRITE=true was set, but the real bunq Payment flow "
                "is not yet enabled in this build. Set BUNQ_LIVE_WRITE=false "
                "to use the safe demo path."
            ),
        )

    # Demo-safe path: record an internal transaction representing the move.
    # This appears in the user's transactions list as a 'self-transfer'.
    now = datetime.now(UTC)
    tx = Transaction(
        bunq_payment_id=f"{bunq_id_prefix}-{int(now.timestamp())}",
        merchant_name="Schijf Buffer (savings)",
        description=f"Agent-proposed transfer: {action_payload.get('rationale', 'commitment savings')}",
        amount=-amount,
        currency="EUR",
        payment_date=now,
        direction=TransactionDirection.OUTGOING,
        is_food_candidate=False,
        food_confidence=0.0,
        merchant_category=MerchantCategory.UNKNOWN,
        created_at=now,
        updated_at=now,
    )
    session.add(tx)
    session.commit()
    session.refresh(tx)
    return {
        "ok": True,
        "executed": "demo",
        "transaction_id": tx.id,
        "amount_eur": amount,
        "message": (
            f"€{amount:.2f} recorded as a transfer to your Schijf Buffer "
            "(demo mode — no real bunq Payment was sent)."
        ),
    }

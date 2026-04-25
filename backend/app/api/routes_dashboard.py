from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import DashboardResponse, MonthlyResponse, ReceiptItemRead
from app.services.goals import active_goal, goal_to_read
from app.services.metrics import (
    elapsed_days_in_month,
    last_purchase_summaries,
    mtd_splits,
    month_bounds,
    top_merchants_by_outside_spend,
    top_outside_items,
    unmatched_food_transactions,
)

router = APIRouter(prefix="/api", tags=["dashboard"])


@router.get("/dashboard", response_model=DashboardResponse)
def dashboard(session: Session = Depends(get_session)):
    today = datetime.now(UTC).date()
    calories, spend = mtd_splits(session, today)
    elapsed = elapsed_days_in_month(today)
    goal = goal_to_read(session, active_goal(session))
    return DashboardResponse(
        month=today.strftime("%Y-%m"),
        elapsed_days_in_month=elapsed,
        calories=calories,
        spend=spend,
        avg_daily_tracked_calories=round(calories.total / elapsed, 2) if elapsed else 0,
        goal=goal,
        last_purchases=last_purchase_summaries(session),
        unmatched_food_transactions=unmatched_food_transactions(session),
    )


@router.get("/monthly", response_model=MonthlyResponse)
def monthly(session: Session = Depends(get_session)):
    today = datetime.now(UTC).date()
    start, end = month_bounds(today)
    calories, spend = mtd_splits(session, today)
    elapsed = elapsed_days_in_month(today)
    goal = goal_to_read(session, active_goal(session))
    risk = "on_track"
    if goal and goal.budget_used_pct >= 1:
        risk = "over_target"
    elif goal and goal.budget_used_pct >= 0.75:
        risk = "watch"
    insight = {
        "summary": f"Outside Schijf spend is EUR {spend.outside_schijf:.2f} this month.",
        "positive_note": "Selected receipt items make the estimate transparent and editable.",
        "one_actionable_tip": "Review the top outside-Schijf item before the next supermarket trip.",
        "risk_level": risk,
    }
    return MonthlyResponse(
        month=today.strftime("%Y-%m"),
        start_date=start.date(),
        end_date=end.date(),
        calories=calories,
        spend=spend,
        avg_daily_tracked_calories=round(calories.total / elapsed, 2) if elapsed else 0,
        top_outside_items_by_calories=[ReceiptItemRead.model_validate(item) for item in top_outside_items(session, "calories_total")],
        top_outside_items_by_spend=[ReceiptItemRead.model_validate(item) for item in top_outside_items(session, "total_price")],
        top_merchants_by_outside_spend=top_merchants_by_outside_spend(session),
        goal=goal,
        insight=insight,
    )


from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models import Goal, GoalMetric
from app.schemas import GoalCreate, GoalRead
from app.services.metrics import mtd_splits


def current_metric_value(session: Session, metric: GoalMetric) -> float:
    calories, spend = mtd_splits(session)
    if metric == GoalMetric.OUTSIDE_SCHIJF_CALORIES:
        return calories.outside_schijf
    return spend.outside_schijf


def active_goal(session: Session) -> Goal | None:
    return session.exec(select(Goal).where(Goal.active == True).order_by(Goal.created_at.desc())).first()  # noqa: E712


def goal_to_read(session: Session, goal: Goal | None) -> GoalRead | None:
    if goal is None:
        return None
    current = current_metric_value(session, goal.metric)
    remaining = max(goal.target_value - current, 0)
    pct = min(current / goal.target_value, 1.0) if goal.target_value else 0.0
    return GoalRead(
        id=goal.id or 0,
        metric=goal.metric,
        reduction_percent=goal.reduction_percent,
        baseline_value=round(goal.baseline_value, 2),
        target_value=round(goal.target_value, 2),
        start_date=goal.start_date,
        active=goal.active,
        current_value=round(current, 2),
        remaining_value=round(remaining, 2),
        budget_used_pct=round(pct, 4),
    )


def create_goal(session: Session, payload: GoalCreate) -> Goal:
    for existing in session.exec(select(Goal).where(Goal.active == True)).all():  # noqa: E712
        existing.active = False
        session.add(existing)

    current = current_metric_value(session, payload.metric)
    baseline = current if current > 0 else (1200.0 if payload.metric == GoalMetric.OUTSIDE_SCHIJF_CALORIES else 120.0)
    target = baseline * (1 - payload.reduction_percent / 100)
    goal = Goal(
        metric=payload.metric,
        reduction_percent=payload.reduction_percent,
        baseline_value=round(baseline, 2),
        target_value=round(target, 2),
        start_date=datetime.now(UTC).date(),
        active=True,
    )
    session.add(goal)
    session.commit()
    session.refresh(goal)
    return goal


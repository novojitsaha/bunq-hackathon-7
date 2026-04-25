from app.models import GoalMetric
from app.schemas import GoalCreate
from app.services.goals import create_goal, goal_to_read


def test_create_goal_uses_default_baseline_when_no_metrics(session):
    goal = create_goal(
        session,
        GoalCreate(metric=GoalMetric.OUTSIDE_SCHIJF_SPEND, reduction_percent=20),
    )
    read = goal_to_read(session, goal)
    assert read is not None
    assert read.baseline_value == 120.0
    assert read.target_value == 96.0
    assert read.remaining_value == 96.0


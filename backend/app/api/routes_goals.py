from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.db import get_session
from app.schemas import GoalCreate, GoalRead
from app.services.goals import active_goal, create_goal, goal_to_read

router = APIRouter(prefix="/api/goals", tags=["goals"])


@router.get("", response_model=GoalRead | None)
def get_active_goal(session: Session = Depends(get_session)):
    return goal_to_read(session, active_goal(session))


@router.post("", response_model=GoalRead)
def post_goal(payload: GoalCreate, session: Session = Depends(get_session)):
    return goal_to_read(session, create_goal(session, payload))


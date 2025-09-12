import logging
from typing import Optional

from fastapi import HTTPException, status
from sqlmodel import Session

from src.api.models.task import Task
from src.api.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VALID_STATUSES = ["initial", "running", "completed", "failed"]

UPDATABLE_STATUSES = ["initial", "failed", "completed"]


def validate_task_ownership(
    task: Task,
    current_user: User,
) -> None:
    if task.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access task {task.id} owned by user {task.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )


def validate_task_state(
    task: Task,
    operation: str,
) -> None:
    if task.status not in UPDATABLE_STATUSES:
        logger.warning(f"Attempted to {operation} task {task.id} in state {task.status}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot {operation} task in {task.status} state",
        )


def validate_temperature(temperature: Optional[float]) -> None:
    if temperature is not None and (temperature < 0 or temperature > 2):
        logger.warning(f"Invalid temperature value: {temperature}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Temperature must be between 0 and 2",
        )


def get_task_or_404(
    task_id: int,
    session: Session,
) -> Task:
    task = session.get(Task, task_id)
    if not task:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    return task
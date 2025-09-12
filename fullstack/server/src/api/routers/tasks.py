import asyncio
import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from src.api.db.session import get_session
from src.api.models.task import (
    AgentSettings, BrowserSettings, Task, TaskCreate, TaskInitiate, TaskRead, TaskSummary
)
from src.api.models.user import User
from src.api.services.auth import get_current_user
from src.api.services.task_validation import (
    get_task_or_404, validate_task_ownership, validate_task_state, validate_temperature
)
from src.api.config import FAILURE_TIME_DELTA_IN_MINUTES

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead)
async def create_task(
    task_data: TaskCreate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    task = Task(
        **task_data.dict(),
        user_id=current_user.id,
    )
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Task created: {task.id} by user: {current_user.id}")
    return task


@router.get("", response_model=List[TaskSummary])
async def get_tasks(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    statement = select(Task).where(Task.user_id == current_user.id)
    tasks = session.exec(statement).all()
    
    return [
        TaskSummary(
            id=task.id,
            task_name=task.task_name,
            status=task.status,
        )
        for task in tasks
    ]


@router.get("/{task_id}", response_model=TaskRead)
async def get_task_by_id(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    task = session.get(Task, task_id)
    
    if not task:
        logger.warning(f"Task not found: {task_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
    
    if task.user_id != current_user.id:
        logger.warning(f"User {current_user.id} attempted to access task {task_id} owned by user {task.user_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this task",
        )
    
    if task.status == "running":
        from datetime import datetime, timezone, timedelta
        
        current_time = datetime.now(timezone.utc)
        
        task_initiated_at = task.initiated_at
        if task_initiated_at.tzinfo is None:
            task_initiated_at = task_initiated_at.replace(tzinfo=timezone.utc)
        
        time_running = current_time - task_initiated_at
        
        if time_running > timedelta(minutes=FAILURE_TIME_DELTA_IN_MINUTES):
            task.status = "failed"
            session.add(task)
            session.commit()
            session.refresh(task)
            
            logger.warning(f"Task {task_id} marked as failed - running for {time_running.total_seconds()/60:.1f} minutes")
    
    return task


@router.patch("/{task_id}/agent-settings", response_model=TaskRead)
async def update_agent_settings(
    task_id: int,
    settings: AgentSettings,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    task = get_task_or_404(task_id, session)
    
    validate_task_ownership(task, current_user)
    
    validate_task_state(task, "update agent settings")
    
    validate_temperature(settings.temperature)
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Agent settings updated for task: {task.id} by user: {current_user.id}")
    return task


@router.patch("/{task_id}/browser-settings", response_model=TaskRead)
async def update_browser_settings(
    task_id: int,
    settings: BrowserSettings,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    task = get_task_or_404(task_id, session)
    
    validate_task_ownership(task, current_user)
    
    validate_task_state(task, "update browser settings")
    
    update_data = settings.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Browser settings updated for task: {task.id} by user: {current_user.id}")
    return task


@router.patch("/{task_id}/initiate", response_model=TaskRead)
async def initiate_task(
    task_id: int,
    task_data: TaskInitiate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    from datetime import datetime, timezone
    from src.api.services.api_key_decrypter import get_api_key_decrypter
    
    task = get_task_or_404(task_id, session)
    
    validate_task_ownership(task, current_user)
    
    validate_task_state(task, "initiate")
    
    decrypted_api_key = None
    if task_data.api_key:
        try:
            decrypter = get_api_key_decrypter()
            decrypted_api_key = decrypter.decrypt_if_encrypted(task_data.api_key)
            logger.info(f"API key processed for task {task_id}")
        except Exception as e:
            logger.error(f"Failed to decrypt API key for task {task_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process API key",
            )
    
    update_data = task_data.dict(exclude={"api_key"})
    for key, value in update_data.items():
        setattr(task, key, value)
    
    task.api_key = None
    
    task.status = "running"
    task.initiated_at = datetime.now(timezone.utc)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Task initiated: {task.id} by user: {current_user.id}")
    logger.info(f"Task details: {task.task_name}, Instruction: {task.instruction}")
    
    from src.api.services.task_execution import start_task_execution
    asyncio.create_task(start_task_execution(task.id, api_key=decrypted_api_key))
    
    return task


@router.patch("/{task_id}/initiate-webui", response_model=TaskRead)
async def initiate_task_with_webui_wrapper(
    task_id: int,
    task_data: TaskInitiate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    from datetime import datetime, timezone
    
    task = get_task_or_404(task_id, session)
    
    validate_task_ownership(task, current_user)
    
    validate_task_state(task, "initiate")
    
    update_data = task_data.dict()
    for key, value in update_data.items():
        setattr(task, key, value)
    
    task.status = "running"
    task.initiated_at = datetime.now(timezone.utc)
    
    session.add(task)
    session.commit()
    session.refresh(task)
    
    logger.info(f"Task initiated with WebUI wrapper: {task.id} by user: {current_user.id}")
    logger.info(f"Task details: {task.task_name}, Instruction: {task.instruction}")
    
    from src.api.services.task_execution import start_task_execution_with_webui_wrapper
    asyncio.create_task(start_task_execution_with_webui_wrapper(task.id))
    
    return task


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    task = get_task_or_404(task_id, session)
    
    validate_task_ownership(task, current_user)
    
    if task.status == "running":
        logger.warning(f"Attempted to delete task {task.id} in running state")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete task in running state",
        )
    
    from src.api.services.result_management import delete_result_with_files
    
    deletion_result = delete_result_with_files(task_id, session)
    
    if not deletion_result["success"]:
        logger.error(f"Failed to delete result for task {task_id}: {deletion_result['errors']}")
    elif deletion_result["warnings"]:
        logger.warning(f"Result deletion completed with warnings for task {task_id}: {deletion_result['warnings']}")
    elif deletion_result["result_found"]:
        logger.info(f"Successfully deleted result and files for task {task_id}")
    else:
        logger.info(f"No result found for task {task_id} - proceeding with task deletion")
    
    session.delete(task)
    session.commit()
    
    logger.info(f"Task deleted: {task_id} by user: {current_user.id}")
    return {"message": "Task deleted successfully"}
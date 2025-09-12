import logging
from typing import Optional
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError
from fastapi import HTTPException, status

from src.api.models.result import Result
from src.api.models.task import Task
from src.api.models.user import User
from src.api.services.task_validation import get_task_or_404, validate_task_ownership

logger = logging.getLogger(__name__)


def get_result_or_404(
    task_id: int,
    session: Session,
) -> Result:
    try:
        logger.debug(f"Attempting to retrieve result for task: {task_id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.error(f"Invalid task_id provided to get_result_or_404: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid task ID",
            )
        
        result = session.get(Result, task_id)
        
        if not result:
            logger.warning(f"Result not found for task: {task_id}")
            logger.info(f"This may indicate the task has not completed or result processing failed")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )
        
        logger.debug(f"Successfully retrieved result for task: {task_id}")
        return result
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error when retrieving result for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
    except Exception as e:
        logger.error(f"Unexpected error when retrieving result for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def validate_task_completed(
    task: Task,
) -> None:
    try:
        if not task:
            logger.error("validate_task_completed called with None task")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            )
        
        logger.debug(f"Validating completion status for task {task.id}: {task.status}")
        
        if task.status != "completed":
            logger.warning(f"Attempted to access results for task {task.id} with status '{task.status}'")
            logger.info(f"Task {task.id} must be completed before results can be accessed")
            
            if task.status == "pending":
                detail = "Task is still pending execution"
            elif task.status == "running":
                detail = "Task is currently running"
            elif task.status == "failed":
                detail = "Task failed to complete"
            else:
                detail = "Task is not completed"
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=detail,
            )
        
        logger.debug(f"Task {task.id} completion status validation passed")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error validating task completion for task {getattr(task, 'id', 'unknown')}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


def validate_result_access(
    task_id: int,
    current_user: User,
    session: Session,
) -> tuple[Task, Result]:
    try:
        logger.info(f"Starting result access validation for task {task_id} by user {current_user.id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.error(f"Invalid task_id in validate_result_access: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid task ID",
            )
        
        if not current_user or not hasattr(current_user, 'id'):
            logger.error("Invalid user object in validate_result_access")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid user authentication",
            )
        
        logger.debug(f"Step 1: Validating task existence for task {task_id}")
        try:
            task = get_task_or_404(task_id, session)
            logger.debug(f"Task {task_id} exists with status: {task.status}")
        except HTTPException as e:
            logger.warning(f"Task validation failed for task {task_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during task validation for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating task",
            )
        
        logger.debug(f"Step 2: Validating task ownership for task {task_id}")
        try:
            validate_task_ownership(task, current_user)
            logger.debug(f"Task {task_id} ownership validation passed for user {current_user.id}")
        except HTTPException as e:
            logger.warning(f"Task ownership validation failed for task {task_id} and user {current_user.id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during ownership validation for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating task ownership",
            )
        
        logger.debug(f"Step 3: Validating task completion for task {task_id}")
        try:
            validate_task_completed(task)
            logger.debug(f"Task {task_id} completion validation passed")
        except HTTPException as e:
            logger.warning(f"Task completion validation failed for task {task_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during completion validation for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating task completion",
            )
        
        logger.debug(f"Step 4: Validating result existence for task {task_id}")
        try:
            result = get_result_or_404(task_id, session)
            logger.debug(f"Result found for task {task_id} with GIF URL: {result.result_gif or 'None'}")
        except HTTPException as e:
            logger.warning(f"Result validation failed for task {task_id}: {e.detail}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during result validation for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating result",
            )
        
        logger.info(f"Result access validation completed successfully for task {task_id}")
        return task, result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error in validate_result_access for task {task_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during result validation",
        )


def check_result_exists(task_id: int, session: Session) -> bool:
    try:
        logger.debug(f"Checking result existence for task: {task_id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.warning(f"Invalid task_id in check_result_exists: {task_id}")
            return False
        
        result = session.get(Result, task_id)
        exists = result is not None
        
        logger.debug(f"Result existence check for task {task_id}: {exists}")
        return exists
        
    except SQLAlchemyError as e:
        logger.error(f"Database error checking result existence for task {task_id}: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking result existence for task {task_id}: {str(e)}")
        return False


def get_result_summary(task_id: int, session: Session) -> Optional[dict]:
    try:
        logger.debug(f"Getting result summary for task: {task_id}")
        
        result = session.get(Result, task_id)
        if not result:
            logger.debug(f"No result found for task {task_id}")
            return None
        
        summary = {
            "task_id": result.task_id,
            "has_gif": result.result_gif is not None,
            "gif_url": result.result_gif,
            "gif_url_length": len(result.result_gif) if result.result_gif else 0,
            "has_script": result.result_json_url is not None,
            "script_url": result.result_json_url,
            "script_url_length": len(result.result_json_url) if result.result_json_url else 0
        }
        
        logger.debug(f"Result summary for task {task_id}: {summary}")
        return summary
        
    except Exception as e:
        logger.error(f"Error getting result summary for task {task_id}: {str(e)}")
        return None
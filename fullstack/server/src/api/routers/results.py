import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.db.session import get_session
from src.api.models.result import ResultRead
from src.api.models.user import User
from src.api.services.auth import get_current_user
from src.api.services.result_validation import validate_result_access, get_result_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/results", tags=["results"])


@router.get("/{task_id}", response_model=ResultRead)
async def get_task_result(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    try:
        logger.info(f"API request: Get result for task {task_id} by user {current_user.id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.warning(f"Invalid task_id received in API: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task ID must be a positive integer",
            )
        
        logger.debug(f"User {current_user.id} ({current_user.username}) requesting result for task {task_id}")
        
        try:
            task, result = validate_result_access(task_id, current_user, session)
            logger.debug(f"Result access validation passed for task {task_id}")
        except HTTPException as e:
            logger.warning(f"Result access validation failed for task {task_id}: {e.detail}")
            
            if e.status_code == status.HTTP_404_NOT_FOUND:
                logger.info(f"Task {task_id} or its result not found - may not exist or result processing may have failed")
            elif e.status_code == status.HTTP_403_FORBIDDEN:
                logger.warning(f"User {current_user.id} attempted to access task {task_id} without permission")
            elif e.status_code == status.HTTP_400_BAD_REQUEST:
                logger.info(f"Task {task_id} is not in completed state - cannot retrieve results")
            
            raise
        except Exception as e:
            logger.error(f"Unexpected error during result access validation for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error validating result access",
            )
        
        try:
            result_summary = get_result_summary(task_id, session)
            if result_summary:
                logger.debug(f"Result summary for task {task_id}: {result_summary}")
        except Exception as e:
            logger.warning(f"Could not get result summary for task {task_id}: {str(e)}")
        
        try:
            response = ResultRead(
                task_id=result.task_id,
                result_gif=result.result_gif,
                result_json_url=result.result_json_url,
            )
            
            logger.info(f"Successfully retrieved result for task {task_id} by user {current_user.id}")
            logger.debug(f"Result has GIF: {result.result_gif is not None}")
            logger.debug(f"Result has script: {result.result_json_url is not None}")
            
            return response
            
        except Exception as e:
            logger.error(f"Error creating response for task {task_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating response",
            )
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in get_task_result for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
    except Exception as e:
        logger.error(f"Critical error in get_task_result for task {task_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.delete("/{task_id}", status_code=status.HTTP_200_OK)
async def delete_task_result(
    task_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Any:
    try:
        logger.info(f"API request: Delete result for task {task_id} by user {current_user.id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.warning(f"Invalid task_id received in delete result API: {task_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Task ID must be a positive integer",
            )
        
        from src.api.services.task_validation import get_task_or_404, validate_task_ownership
        task = get_task_or_404(task_id, session)
        validate_task_ownership(task, current_user)
        
        from src.api.services.result_management import delete_result_with_files
        deletion_result = delete_result_with_files(task_id, session)
        
        if deletion_result["success"]:
            if deletion_result["result_found"]:
                message = "Result and associated files deleted successfully"
                if deletion_result["warnings"]:
                    message += f" (with warnings: {', '.join(deletion_result['warnings'])})"
                logger.info(f"Successfully deleted result for task {task_id} by user {current_user.id}")
            else:
                message = "No result found for this task"
                logger.info(f"No result found to delete for task {task_id} by user {current_user.id}")
        else:
            logger.error(f"Failed to delete result for task {task_id}: {deletion_result['errors']}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete result: {', '.join(deletion_result['errors'])}",
            )
        
        return {
            "message": message,
            "task_id": task_id,
            "files_deleted": deletion_result["files_deleted"],
            "database_deleted": deletion_result["database_deleted"],
            "warnings": deletion_result["warnings"]
        }
        
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error(f"Database error in delete_task_result for task {task_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred",
        )
    except Exception as e:
        logger.error(f"Critical error in delete_task_result for task {task_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/health", include_in_schema=False)
async def health_check():
    try:
        logger.debug("Results router health check requested")
        return {
            "status": "healthy",
            "service": "results",
            "message": "Results API is operational"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed",
        )
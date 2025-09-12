import logging
from typing import Dict, Any

from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError

from src.api.models.result import Result
from src.api.services.cloudinary_service import cloudinary_service

logger = logging.getLogger(__name__)


def delete_result_with_files(task_id: int, session: Session) -> Dict[str, Any]:
    operation_result = {
        "success": False,
        "result_found": False,
        "files_deleted": False,
        "database_deleted": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        logger.info(f"Starting result deletion process for task {task_id}")
        
        result = session.get(Result, task_id)
        if not result:
            logger.info(f"No result found for task {task_id} - nothing to delete")
            operation_result["success"] = True
            return operation_result
        
        operation_result["result_found"] = True
        logger.info(f"Found result record for task {task_id}")
        
        logger.info(f"Deleting Cloudinary files for task {task_id}")
        file_deletion_results = cloudinary_service.delete_task_files(task_id)
        
        if file_deletion_results["errors"]:
            error_msg = f"Some files could not be deleted from Cloudinary for task {task_id}"
            logger.warning(f"{error_msg}: {file_deletion_results['errors']}")
            operation_result["warnings"].extend(file_deletion_results["errors"])
        
        operation_result["files_deleted"] = (
            file_deletion_results["gif_deleted"] or 
            file_deletion_results["script_deleted"] or 
            not file_deletion_results["errors"]
        )
        
        if operation_result["files_deleted"]:
            logger.info(f"Successfully processed Cloudinary file deletion for task {task_id}")
        
        try:
            logger.info(f"Deleting result record from database for task {task_id}")
            session.delete(result)
            session.commit()
            operation_result["database_deleted"] = True
            logger.info(f"Successfully deleted result record for task {task_id}")
        except SQLAlchemyError as e:
            error_msg = f"Database error when deleting result for task {task_id}: {str(e)}"
            logger.error(error_msg)
            operation_result["errors"].append(error_msg)
            session.rollback()
            return operation_result
        
        operation_result["success"] = True
        logger.info(f"Completed result deletion process for task {task_id}")
        
    except Exception as e:
        error_msg = f"Unexpected error during result deletion for task {task_id}: {str(e)}"
        logger.error(error_msg)
        operation_result["errors"].append(error_msg)
        try:
            session.rollback()
        except Exception as rollback_error:
            logger.error(f"Error during rollback for task {task_id}: {rollback_error}")
    
    return operation_result


def cleanup_orphaned_files(task_id: int) -> Dict[str, Any]:
    logger.info(f"Starting orphaned file cleanup for task {task_id}")
    
    file_deletion_results = cloudinary_service.delete_task_files(task_id)
    
    cleanup_result = {
        "success": True,
        "files_deleted": file_deletion_results["gif_deleted"] or file_deletion_results["script_deleted"],
        "errors": file_deletion_results["errors"]
    }
    
    if cleanup_result["errors"]:
        logger.warning(f"Orphaned file cleanup completed with errors for task {task_id}: {cleanup_result['errors']}")
        cleanup_result["success"] = False
    else:
        logger.info(f"Successfully completed orphaned file cleanup for task {task_id}")
    
    return cleanup_result


def get_result_file_status(task_id: int, session: Session) -> Dict[str, Any]:
    status = {
        "result_exists": False,
        "has_gif_url": False,
        "has_script_url": False,
        "gif_url": None,
        "script_url": None
    }
    
    try:
        result = session.get(Result, task_id)
        if result:
            status["result_exists"] = True
            status["has_gif_url"] = result.result_gif is not None
            status["has_script_url"] = result.result_json_url is not None
            status["gif_url"] = result.result_gif
            status["script_url"] = result.result_json_url
            
            logger.debug(f"Result file status for task {task_id}: {status}")
    except Exception as e:
        logger.error(f"Error checking result file status for task {task_id}: {str(e)}")
    
    return status 
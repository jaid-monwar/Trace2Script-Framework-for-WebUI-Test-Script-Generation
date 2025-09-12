import os
import logging
import tempfile
from typing import Optional, Tuple

from sqlmodel import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

from src.api.db.session import engine
from src.api.models.result import Result
from src.api.services.cloudinary_service import cloudinary_service
from src.api.services.script_conversion_service import convert_agent_history_to_script

logger = logging.getLogger(__name__)


async def create_task_result(task_id: int, gif_path: Optional[str] = None) -> bool:
    try:
        logger.info(f"Starting result processing for task {task_id}")
        
        if not isinstance(task_id, int) or task_id <= 0:
            logger.error(f"Invalid task_id provided: {task_id}")
            return False
        
        if gif_path is None:
            gif_path = f"./tmp/agent_history/task_{task_id}/task_{task_id}.gif"
            logger.debug(f"Using default GIF path for task {task_id}: {gif_path}")
        
        result_gif_url = None
        result_json_url = None
        gif_upload_attempted = False
        gif_upload_successful = False
        script_upload_attempted = False
        script_upload_successful = False
        
        if not cloudinary_service.is_available():
            reason = cloudinary_service.get_unavailability_reason()
            logger.warning(f"Cloudinary service unavailable for task {task_id}: {reason}")
            logger.info(f"Proceeding with result creation without file upload for task {task_id}")
        
        agent_history_path = f"./tmp/agent_history/task_{task_id}/task_{task_id}.json"
        if os.path.exists(agent_history_path):
            logger.info(f"Agent history JSON found for task {task_id}: {agent_history_path}")
            
            try:
                logger.info(f"Converting agent history to script for task {task_id}")
                script_content = await convert_agent_history_to_script(agent_history_path, task_id)
                
                if script_content:
                    logger.info(f"Successfully converted agent history to script for task {task_id}")
                    
                    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                        temp_file.write(script_content)
                        temp_script_path = temp_file.name
                    
                    logger.debug(f"Temporary script file created for task {task_id}: {temp_script_path}")
                    
                    if cloudinary_service.is_available():
                        script_upload_attempted = True
                        logger.info(f"Attempting Cloudinary script upload for task {task_id}")
                        
                        try:
                            result_json_url = cloudinary_service.upload_script(temp_script_path, task_id)
                            
                            if result_json_url:
                                script_upload_successful = True
                                logger.info(f"Successfully uploaded script for task {task_id}: {result_json_url}")
                            else:
                                logger.error(f"Failed to upload script for task {task_id}")
                                
                        except Exception as e:
                            logger.error(f"Error during script upload for task {task_id}: {str(e)}")
                            logger.error(f"Script upload error details: {type(e).__name__}: {str(e)}")
                    else:
                        logger.info(f"Skipping script upload for task {task_id} - Cloudinary service unavailable")
                    
                    try:
                        os.unlink(temp_script_path)
                        logger.debug(f"Cleaned up temporary script file for task {task_id}")
                    except Exception as e:
                        logger.warning(f"Failed to clean up temporary script file for task {task_id}: {str(e)}")
                        
                else:
                    logger.warning(f"Failed to convert agent history to script for task {task_id}")
                    
            except Exception as e:
                logger.error(f"Error during script conversion for task {task_id}: {str(e)}")
                logger.error(f"Script conversion error details: {type(e).__name__}: {str(e)}")
        else:
            logger.info(f"No agent history JSON found for task {task_id} at {agent_history_path}")
        
        if os.path.exists(gif_path):
            logger.info(f"GIF file found for task {task_id}: {gif_path}")
            
            try:
                file_size = os.path.getsize(gif_path)
                if file_size == 0:
                    logger.warning(f"GIF file is empty for task {task_id}: {gif_path}")
                else:
                    logger.debug(f"GIF file size for task {task_id}: {file_size} bytes")
                    
                    if cloudinary_service.is_available():
                        gif_upload_attempted = True
                        logger.info(f"Attempting Cloudinary GIF upload for task {task_id}")
                        
                        try:
                            result_gif_url = cloudinary_service.upload_gif(gif_path, task_id)
                            
                            if result_gif_url:
                                gif_upload_successful = True
                                logger.info(f"Successfully uploaded GIF for task {task_id}: {result_gif_url}")
                                
                                cleanup_success = cloudinary_service.delete_local_file(gif_path, task_id)
                                if not cleanup_success:
                                    logger.warning(f"Failed to delete local GIF file for task {task_id}, but upload was successful")
                                    logger.warning(f"Manual cleanup may be required for: {gif_path}")
                            else:
                                logger.error(f"Failed to upload GIF for task {task_id}, keeping local file")
                                
                        except Exception as e:
                            logger.error(f"Error during GIF upload for task {task_id}: {str(e)}")
                            logger.error(f"Upload error details: {type(e).__name__}: {str(e)}")
                    else:
                        logger.info(f"Skipping GIF upload for task {task_id} - Cloudinary service unavailable")
                        
            except Exception as e:
                logger.error(f"Error validating GIF file for task {task_id}: {str(e)}")
                
        else:
            logger.info(f"No GIF file found for task {task_id} at {gif_path}")
        
        database_success = False
        try:
            logger.info(f"Creating/updating result record for task {task_id}")
            
            with Session(engine) as session:
                existing_result = session.get(Result, task_id)
                
                if existing_result:
                    old_gif_url = existing_result.result_gif
                    old_json_url = existing_result.result_json_url
                    existing_result.result_gif = result_gif_url
                    existing_result.result_json_url = result_json_url
                    session.add(existing_result)
                    logger.info(f"Updated existing result record for task {task_id}")
                    if old_gif_url != result_gif_url:
                        logger.info(f"GIF URL changed for task {task_id}: {old_gif_url} -> {result_gif_url}")
                    if old_json_url != result_json_url:
                        logger.info(f"Script URL changed for task {task_id}: {old_json_url} -> {result_json_url}")
                else:
                    result = Result(
                        task_id=task_id,
                        result_gif=result_gif_url,
                        result_json_url=result_json_url
                    )
                    session.add(result)
                    logger.info(f"Created new result record for task {task_id}")
                
                session.commit()
                database_success = True
                logger.info(f"Successfully saved result record for task {task_id}")
                
        except IntegrityError as e:
            logger.error(f"Database integrity error for task {task_id}: {str(e)}")
            logger.error("This may indicate a foreign key constraint violation")
            return False
        except SQLAlchemyError as e:
            logger.error(f"Database error when creating result for task {task_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected database error for task {task_id}: {str(e)}")
            return False
        
        _log_result_processing_summary(task_id, gif_upload_attempted, gif_upload_successful, script_upload_attempted, script_upload_successful, database_success, result_gif_url, result_json_url)
        
        logger.info(f"Result processing completed for task {task_id}")
        return database_success
        
    except Exception as e:
        logger.error(f"Critical error during result processing for task {task_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        return False


def process_task_result_safe(task_id: int, gif_path: Optional[str] = None) -> None:
    import asyncio
    
    try:
        logger.info(f"Starting safe result processing for task {task_id}")
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, create_task_result(task_id, gif_path))
                    success = future.result()
            else:
                success = loop.run_until_complete(create_task_result(task_id, gif_path))
        except RuntimeError:
            success = asyncio.run(create_task_result(task_id, gif_path))
        
        if success:
            logger.info(f"Result processing completed successfully for task {task_id}")
        else:
            logger.warning(f"Result processing failed for task {task_id}")
            logger.warning("Task completion status remains unaffected by result processing failure")
            
    except Exception as e:
        logger.error(f"Critical error in safe result processing for task {task_id}: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        logger.error("Task completion status is unaffected by this error")
        
        if gif_path:
            logger.error(f"GIF path involved: {gif_path}")


def get_gif_path_for_task(task_id: int) -> str:
    if not isinstance(task_id, int) or task_id <= 0:
        logger.warning(f"Invalid task_id provided to get_gif_path_for_task: {task_id}")
        return ""
    
    path = f"./tmp/agent_history/task_{task_id}/task_{task_id}.gif"
    logger.debug(f"Generated GIF path for task {task_id}: {path}")
    return path


def check_gif_exists(task_id: int) -> bool:
    try:
        gif_path = get_gif_path_for_task(task_id)
        if not gif_path:
            logger.warning(f"Could not generate GIF path for task {task_id}")
            return False
        
        exists = os.path.exists(gif_path)
        logger.debug(f"GIF file existence check for task {task_id}: {exists} at {gif_path}")
        
        if exists:
            try:
                file_size = os.path.getsize(gif_path)
                logger.debug(f"GIF file size for task {task_id}: {file_size} bytes")
                if file_size == 0:
                    logger.warning(f"GIF file exists but is empty for task {task_id}")
            except Exception as e:
                logger.warning(f"Could not check GIF file size for task {task_id}: {str(e)}")
        
        return exists
        
    except Exception as e:
        logger.error(f"Error checking GIF existence for task {task_id}: {str(e)}")
        return False


def _log_result_processing_summary(
    task_id: int, 
    gif_upload_attempted: bool, 
    gif_upload_successful: bool, 
    script_upload_attempted: bool,
    script_upload_successful: bool,
    database_success: bool, 
    result_gif_url: Optional[str],
    result_json_url: Optional[str]
) -> None:
    logger.info(f"Result processing summary for task {task_id}:")
    logger.info(f"  - GIF upload attempted: {gif_upload_attempted}")
    logger.info(f"  - GIF upload successful: {gif_upload_successful}")
    logger.info(f"  - Script upload attempted: {script_upload_attempted}")
    logger.info(f"  - Script upload successful: {script_upload_successful}")
    logger.info(f"  - Database operation successful: {database_success}")
    logger.info(f"  - Final GIF URL: {result_gif_url or 'None'}")
    logger.info(f"  - Final script URL: {result_json_url or 'None'}")
    
    if gif_upload_attempted and not gif_upload_successful:
        logger.warning(f"GIF upload was attempted but failed for task {task_id}")
    
    if script_upload_attempted and not script_upload_successful:
        logger.warning(f"Script upload was attempted but failed for task {task_id}")
    
    if not database_success:
        logger.error(f"Database operation failed for task {task_id}")


def validate_result_processing_environment() -> Tuple[bool, list]:
    issues = []
    
    if not cloudinary_service.is_available():
        reason = cloudinary_service.get_unavailability_reason()
        issues.append(f"Cloudinary service unavailable: {reason}")
    
    base_dir = "./tmp/agent_history"
    if not os.path.exists(base_dir):
        issues.append(f"Agent history directory does not exist: {base_dir}")
    elif not os.access(base_dir, os.W_OK):
        issues.append(f"No write permission to agent history directory: {base_dir}")
    
    try:
        with Session(engine) as session:
            session.execute("SELECT 1")
        logger.debug("Database connectivity check passed")
    except Exception as e:
        issues.append(f"Database connectivity issue: {str(e)}")
    
    is_valid = len(issues) == 0
    
    if is_valid:
        logger.info("Result processing environment validation passed")
    else:
        logger.warning(f"Result processing environment validation failed: {len(issues)} issues found")
        for issue in issues:
            logger.warning(f"  - {issue}")
    
    return is_valid, issues
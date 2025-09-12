import os
import logging
from typing import Optional
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from ..config import get_cloudinary_config

logger = logging.getLogger(__name__)


class CloudinaryService:
    
    def __init__(self):
        self.is_configured = False
        self.config_error = None
        
        try:
            config = get_cloudinary_config()
            if config:
                cloudinary.config(**config)
                self.is_configured = True
                logger.info("Cloudinary service initialized successfully")
            else:
                self.config_error = "Cloudinary credentials are missing or incomplete"
                logger.warning(f"Cloudinary service initialization failed: {self.config_error}")
                logger.warning("File upload functionality will be disabled")
        except Exception as e:
            self.config_error = f"Failed to initialize Cloudinary configuration: {str(e)}"
            logger.error(f"Cloudinary service initialization error: {self.config_error}")
            logger.error("File upload functionality will be disabled")
    
    def is_available(self) -> bool:
        return self.is_configured
    
    def get_unavailability_reason(self) -> Optional[str]:
        return self.config_error if not self.is_configured else None
    
    def upload_file(self, file_path: str, task_id: int, file_type: str = "gif") -> Optional[str]:
        if not self.is_configured:
            logger.warning(f"Skipping Cloudinary upload for task {task_id}: {self.config_error}")
            return None
        
        if not os.path.exists(file_path):
            logger.info(f"{file_type.upper()} file not found at {file_path} for task {task_id} - skipping upload")
            return None
        
        try:
            file_size = os.path.getsize(file_path)
            if file_size == 0:
                logger.warning(f"{file_type.upper()} file is empty for task {task_id}: {file_path}")
                return None
            logger.debug(f"{file_type.upper()} file size for task {task_id}: {file_size} bytes")
        except Exception as e:
            logger.error(f"Error checking {file_type.upper()} file for task {task_id}: {str(e)}")
            return None
        
        if file_type == "gif":
            resource_type = "image"
            public_id = f"task_{task_id}_result"
        elif file_type == "script":
            resource_type = "raw"
            public_id = f"task_{task_id}_script"
        else:
            logger.error(f"Unsupported file type: {file_type}")
            return None
        
        max_retries = 2
        for attempt in range(max_retries):
            try:
                logger.info(f"Starting Cloudinary {file_type.upper()} upload for task {task_id} (attempt {attempt + 1}/{max_retries})")
                
                upload_result = cloudinary.uploader.upload(
                    file_path,
                    resource_type=resource_type,
                    public_id=public_id,
                    overwrite=True,
                    invalidate=True,
                    timeout=60
                )
                
                public_url = upload_result.get('secure_url')
                
                if public_url:
                    logger.info(f"Successfully uploaded {file_type.upper()} for task {task_id}: {public_url}")
                    logger.debug(f"Upload details for task {task_id}: {upload_result}")
                    return public_url
                else:
                    logger.error(f"Upload completed but no secure_url returned for task {task_id}")
                    logger.error(f"Upload result: {upload_result}")
                    return None
                    
            except CloudinaryError as e:
                logger.error(f"Cloudinary {file_type.upper()} upload failed for task {task_id} (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All {file_type.upper()} upload attempts failed for task {task_id}")
                    return None
                else:
                    logger.info(f"Retrying {file_type.upper()} upload for task {task_id}...")
                    
            except Exception as e:
                logger.error(f"Unexpected error during {file_type.upper()} upload for task {task_id} (attempt {attempt + 1}): {str(e)}")
                if attempt == max_retries - 1:
                    logger.error(f"All {file_type.upper()} upload attempts failed for task {task_id} due to unexpected errors")
                    return None
                else:
                    logger.info(f"Retrying {file_type.upper()} upload for task {task_id} after unexpected error...")
        
        return None
    
    def upload_gif(self, file_path: str, task_id: int) -> Optional[str]:
        return self.upload_file(file_path, task_id, "gif")
    
    def upload_script(self, file_path: str, task_id: int) -> Optional[str]:
        return self.upload_file(file_path, task_id, "script")
    
    def delete_local_file(self, file_path: str, task_id: int) -> bool:
        try:
            if not os.path.exists(file_path):
                logger.debug(f"Local file already deleted or doesn't exist for task {task_id}: {file_path}")
                return True
            
            if not os.access(file_path, os.W_OK):
                logger.error(f"No write permission to delete local file for task {task_id}: {file_path}")
                return False
            
            os.remove(file_path)
            logger.info(f"Successfully deleted local GIF file for task {task_id}: {file_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission denied when deleting local file for task {task_id}: {file_path} - {str(e)}")
            return False
        except FileNotFoundError:
            logger.debug(f"Local file already deleted for task {task_id}: {file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete local file {file_path} for task {task_id}: {str(e)}")
            return False
    
    def delete_cloudinary_file(self, public_id: str, resource_type: str = "image") -> bool:
        if not self.is_configured:
            logger.warning(f"Skipping Cloudinary deletion: {self.config_error}")
            return False
        
        try:
            logger.info(f"Deleting Cloudinary file: {public_id} (resource_type: {resource_type})")
            
            result = cloudinary.uploader.destroy(
                public_id,
                resource_type=resource_type,
                invalidate=True
            )
            
            if result.get('result') == 'ok':
                logger.info(f"Successfully deleted Cloudinary file: {public_id}")
                return True
            elif result.get('result') == 'not found':
                logger.info(f"Cloudinary file not found (already deleted?): {public_id}")
                return True
            else:
                logger.warning(f"Cloudinary deletion returned unexpected result for {public_id}: {result}")
                return False
                
        except CloudinaryError as e:
            logger.error(f"Cloudinary error when deleting {public_id}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error when deleting Cloudinary file {public_id}: {str(e)}")
            return False
    
    def delete_task_files(self, task_id: int) -> dict:
        results = {
            "gif_deleted": False,
            "script_deleted": False,
            "errors": []
        }
        
        if not self.is_configured:
            error_msg = f"Cannot delete files for task {task_id}: {self.config_error}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
            return results
        
        logger.info(f"Deleting all Cloudinary files for task {task_id}")
        
        gif_public_id = f"task_{task_id}_result"
        try:
            results["gif_deleted"] = self.delete_cloudinary_file(gif_public_id, "image")
        except Exception as e:
            error_msg = f"Error deleting GIF for task {task_id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        script_public_id = f"task_{task_id}_script"
        try:
            results["script_deleted"] = self.delete_cloudinary_file(script_public_id, "raw")
        except Exception as e:
            error_msg = f"Error deleting script for task {task_id}: {str(e)}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
        
        if results["gif_deleted"] and results["script_deleted"] and not results["errors"]:
            logger.info(f"Successfully deleted all Cloudinary files for task {task_id}")
        elif results["errors"]:
            logger.warning(f"Completed file deletion for task {task_id} with errors: {results['errors']}")
        else:
            logger.info(f"Completed file deletion for task {task_id} - some files may not have existed")
        
        return results


try:
    cloudinary_service = CloudinaryService()
    logger.debug("Cloudinary service singleton created")
except Exception as e:
    logger.error(f"Failed to create Cloudinary service singleton: {str(e)}")
    cloudinary_service = CloudinaryService()
    cloudinary_service.is_configured = False
    cloudinary_service.config_error = f"Service initialization failed: {str(e)}"
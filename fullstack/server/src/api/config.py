import os
import logging
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/auth_db")

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "1440"))

API_PREFIX = os.getenv("API_PREFIX", "/api/v1")

CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
FAILURE_TIME_DELTA_IN_MINUTES=10

def validate_cloudinary_config() -> bool:
    required_vars = [
        ("CLOUDINARY_CLOUD_NAME", CLOUDINARY_CLOUD_NAME),
        ("CLOUDINARY_API_KEY", CLOUDINARY_API_KEY),
        ("CLOUDINARY_API_SECRET", CLOUDINARY_API_SECRET)
    ]
    
    missing_vars = []
    for var_name, var_value in required_vars:
        if not var_value or var_value.strip() == "":
            missing_vars.append(var_name)
    
    if missing_vars:
        logger.warning(f"Missing Cloudinary configuration variables: {', '.join(missing_vars)}")
        logger.warning("Cloudinary file upload functionality will be disabled")
        return False
    
    logger.info("Cloudinary configuration validated successfully")
    return True

def get_cloudinary_config() -> Optional[dict]:
    try:
        if validate_cloudinary_config():
            config = {
                "cloud_name": CLOUDINARY_CLOUD_NAME,
                "api_key": CLOUDINARY_API_KEY,
                "api_secret": CLOUDINARY_API_SECRET
            }
            logger.debug("Cloudinary configuration retrieved successfully")
            return config
        else:
            logger.warning("Cloudinary configuration is incomplete - file uploads will be skipped")
            return None
    except Exception as e:
        logger.error(f"Error retrieving Cloudinary configuration: {str(e)}")
        return None
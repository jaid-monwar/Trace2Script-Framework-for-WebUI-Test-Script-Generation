import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends

from src.api.models.user import User
from src.api.services.auth import get_current_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(tags=["hello"])


@router.get("/hello")
async def hello_world() -> Dict[str, str]:
    return {"message": "Hello, World!"}


@router.get("/hello/protected")
async def hello_protected(current_user: User = Depends(get_current_user)) -> Dict[str, Any]:
    return {
        "message": f"Hello, {current_user.username}!",
        "user_id": current_user.id,
        "protected": True,
    }
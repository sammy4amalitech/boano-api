from fastapi import APIRouter

from .autogen import router as autogen_router
from .users import router as users_router
from .time_log import router as time_log_router
from .webhook import router as webhook_router

router = APIRouter(prefix="/v1")
router.include_router(users_router)
router.include_router(autogen_router)
router.include_router(time_log_router)
router.include_router(webhook_router)
from fastapi import APIRouter
# ...existing code...
from app.api.v1 import autogen

router = APIRouter(prefix="/v1")
# ...existing code...
router.include_router(autogen.router, prefix="/autogen", tags=["autogen"])

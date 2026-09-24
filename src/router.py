from fastapi import APIRouter

from app.api.v1 import endpoints  # noqa: F401
from app.api.v1.router import router as v1_router

router = APIRouter(prefix="/api")
router.include_router(v1_router)

from fastapi import APIRouter

from app.api.v1.endpoints.analyze import router as analyze_router

router = APIRouter(prefix="/v1")
router.include_router(analyze_router)

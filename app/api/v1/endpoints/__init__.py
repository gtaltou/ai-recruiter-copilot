from fastapi import APIRouter

from app.api.v1.endpoints.analyses import router as analyses_router

router = APIRouter(prefix="/v1")
router.include_router(analyses_router)

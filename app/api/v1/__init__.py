from fastapi import APIRouter
from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.export import router as export_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(analyze_router)
v1_router.include_router(export_router)
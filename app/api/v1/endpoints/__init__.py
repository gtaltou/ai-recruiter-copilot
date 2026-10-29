from fastapi import APIRouter
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.analyze import router as analyze_router
from app.api.v1.endpoints.export import router as export_router

v1_router = APIRouter()
v1_router.include_router(health_router)
v1_router.include_router(analyze_router)
v1_router.include_router(export_router)

__all__ = ["v1_router"]

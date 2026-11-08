from fastapi import APIRouter
from app.api.v1.endpoints import health, analyze, export

v1_router = APIRouter()

v1_router.include_router(health.router, tags=["health"])
v1_router.include_router(analyze.router, tags=["analyze"])
v1_router.include_router(export.router, tags=["export"])
from app.api.v1.endpoints import analyses
v1_router.include_router(analyses.router, tags=['analyses'])

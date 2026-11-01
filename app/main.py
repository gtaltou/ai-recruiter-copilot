from fastapi import FastAPI
from app.api.v1.api import v1_router
from app.core.config import settings
from app.core.middleware import MetricsMiddleware, LoggingMiddleware, JWTAuthMiddleware
from app.core.logging import setup_logging

app = FastAPI(title=settings.APP_NAME)

setup_logging(log_level=settings.LOG_LEVEL, log_json=settings.LOG_JSON)

app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(JWTAuthMiddleware)

app.include_router(v1_router, prefix="/api/v1")

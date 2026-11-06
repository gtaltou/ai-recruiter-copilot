from fastapi import FastAPI
from app.api.v1.api import v1_router
from app.core.config import settings
from app.core.middleware import MetricsMiddleware, LoggingMiddleware, JWTAuthMiddleware
from app.core.logging import setup_logging
from fastapi.staticfiles import StaticFiles
from app.web.router import router as web_router


app = FastAPI(title=settings.APP_NAME)

setup_logging(log_level=settings.LOG_LEVEL, log_json=settings.LOG_JSON)

app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(JWTAuthMiddleware)

app.include_router(v1_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_router)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import v1_router
from app.core.config import settings
from app.core.middleware import MetricsMiddleware, LoggingMiddleware, JWTAuthMiddleware
from app.core.logging import setup_logging
from app.db import engine, Base
from app.web.router import router as web_router





@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup : logging + création des tables."""
    setup_logging(log_level=settings.LOG_LEVEL, log_json=settings.LOG_JSON)
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

app.add_middleware(MetricsMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(JWTAuthMiddleware)

app.include_router(v1_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(web_router)



from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1 import router as v1_router
import logging

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Agent autonome de sourcing et d'évaluation de candidats",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(v1_router, prefix="/api")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "llm_provider": settings.LLM_PROVIDER,
    }

@app.get("/")
async def root():
    return {
        "message": "AI Recruiter Copilot API",
        "docs": "/docs",
    }

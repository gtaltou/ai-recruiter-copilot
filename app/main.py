from fastapi import FastAPI
from app.api.v1 import v1_router
from app.core.middleware import setup_middlewares

app = FastAPI(
    title="AI Recruiter Copilot API",
    description="Analyse sémantique de CV par rapport à des descriptions de poste",
    version="3.0.0",
)

setup_middlewares(app)
app.include_router(v1_router, prefix="/api")

@app.get("/health")
async def health():
    return {"status": "healthy", "version": "3.0.0"}

@app.get("/ping")
async def ping():
    return {"ping": "pong"}
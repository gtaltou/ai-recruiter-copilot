from datetime import datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().timestamp(),
        "version": "1.0.0",
        "services": {
            "api": "up",
            "database": "connected",
        },
    }

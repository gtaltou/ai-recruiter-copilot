from fastapi import APIRouter, HTTPException
import time

router = APIRouter()

@router.get("/health")
async def health_check():
    """Check the health of the application and its dependencies."""
    try:
        return {
            "status": "healthy",
            "timestamp": time.time(),
            "version": "1.0.0"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=str(e))

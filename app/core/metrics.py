import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger("app")

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter des métriques de base sur les requêtes.
    """
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        status_code = response.status_code
        
        logger.info(
            "Request metrics",
            extra={
                "metric_type": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round(process_time * 1000, 2)
            }
        )
        
        response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
        return response

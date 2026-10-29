import time
import json
import logging
from uuid import uuid4
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("ai-recruiter-copilot")
metrics_logger = logging.getLogger("app.metrics")


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid4())
        request.state.request_id = request_id
        logger.info("Incoming request", extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
        })
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        logger.info("Outgoing response", extra={
            "request_id": request_id,
            "status_code": response.status_code,
            "elapsed_seconds": round(elapsed, 4),
        })
        response.headers["X-Request-ID"] = request_id
        return response


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        elapsed = time.time() - start_time
        metrics_logger.info("Metrics", extra={
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "elapsed_seconds": round(elapsed, 4),
        })
        response.headers["X-Process-Time"] = str(round(elapsed, 4))
        return response

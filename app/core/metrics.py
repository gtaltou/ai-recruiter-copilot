import time
import logging

from fastapi import Request
from prometheus_client import Counter, Histogram, Gauge
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

logger = logging.getLogger(__name__)

# Métriques Prometheus
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["endpoint", "method", "status_code"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["endpoint", "method"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

http_requests_in_progress = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests in progress",
    ["endpoint", "method"],
)

app_info = Gauge(
    "app_info",
    "Application metadata",
    ["name", "version"],
)

analyses_total = Counter(
    "analyses_total",
    "Total number of analyses performed",
)

APP_INFO = app_info
CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"


def generate_latest():
    from prometheus_client import generate_latest as _gen
    return _gen()


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter des métriques de base sur les requêtes.
    Enregistre la latence et les codes de statut.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()
        http_requests_in_progress.labels(
            endpoint=request.url.path, method=request.method
        ).inc()

        try:
            response = await call_next(request)
        finally:
            http_requests_in_progress.labels(
                endpoint=request.url.path, method=request.method
            ).dec()

        process_time = time.perf_counter() - start_time
        status_code = response.status_code

        # Métriques Prometheus
        http_requests_total.labels(
            endpoint=request.url.path,
            method=request.method,
            status_code=str(status_code),
        ).inc()
        http_request_duration_seconds.labels(
            endpoint=request.url.path, method=request.method
        ).observe(process_time)

        # Log structuré
        logger.info(
            "Request metrics",
            extra={
                "metric_type": "http_request",
                "method": request.method,
                "path": request.url.path,
                "status_code": status_code,
                "latency_ms": round(process_time * 1000, 2),
            }
        )

        response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
        return response

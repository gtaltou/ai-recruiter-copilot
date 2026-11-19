import time
from typing import Callable
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
import logging

# === NOUVEAU : Import Prometheus ===
from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import PlainTextResponse

logger = logging.getLogger("app")

# === NOUVEAU : Définition des métriques Prometheus ===

HTTP_REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "endpoint", "status_code"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

HTTP_IN_PROGRESS = Gauge(
    "http_requests_in_progress",
    "Number of HTTP requests currently in progress",
    labelnames=["method", "endpoint"],
)

ANALYSES_TOTAL = Counter(
    "analyses_total",
    "Total number of CV analyses performed",
    labelnames=["status"],
)

APP_INFO = Info("app", "Application metadata")


# === NOUVEAU : Fonction helper pour normaliser les endpoints ===

def _normalize_endpoint(path: str) -> str:
    """Évite la cardinalité élevée : /analyses/123 -> /analyses/{id}"""
    parts = path.strip("/").split("/")
    normalized = []
    for part in parts:
        if part.isdigit():
            normalized.append("{id}")
        else:
            normalized.append(part)
    return "/" + "/".join(normalized)


# === MODIFIÉ : Ton middleware enrichi avec Prometheus ===

class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware pour collecter des métriques de base sur les requêtes.
    """
    async def dispatch(self, request: Request, call_next: Callable):
        start_time = time.perf_counter()

        # Prometheus : requête en cours
        endpoint = _normalize_endpoint(request.url.path)
        HTTP_IN_PROGRESS.labels(method=request.method, endpoint=endpoint).inc()

        try:
            response = await call_next(request)
            process_time = time.perf_counter() - start_time
            status_code = response.status_code

            # Log structuré (déjà existant)
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

            # Prometheus : enregistrer la métrique
            HTTP_REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION.labels(
                method=request.method,
                endpoint=endpoint,
                status_code=str(status_code)
            ).observe(process_time)

            response.headers["X-Process-Time-Ms"] = str(round(process_time * 1000, 2))
            return response

        except Exception as exc:
            process_time = time.perf_counter() - start_time
            HTTP_REQUEST_COUNT.labels(
                method=request.method,
                endpoint=endpoint,
                status_code="500"
            ).inc()
            raise
        finally:
            HTTP_IN_PROGRESS.labels(method=request.method, endpoint=endpoint).dec()

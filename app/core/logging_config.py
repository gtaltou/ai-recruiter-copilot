import logging
import sys
import uuid
from contextvars import ContextVar
from datetime import datetime, timezone

from pythonjsonlogger import jsonlogger

# ContextVar pour propager le request_id dans toute la requête
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class RequestIdFilter(logging.Filter):
    """Ajoute request_id et user_id à chaque enregistrement de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True


def setup_logging() -> None:
    """Configure le logging structuré JSON pour toute l'application."""
    log_level = logging.getLevelName("INFO")

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)

    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(user_id)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    # Éviter les doublons de handlers
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Réduire le bruit des bibliothèques tierces
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)

    logging.info("Structured JSON logging configured", extra={"event": "startup"})


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger avec le nom du module."""
    return logging.getLogger(name)

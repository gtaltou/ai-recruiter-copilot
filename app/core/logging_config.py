"""Configuration de logging structuré pour l'application."""

import logging
import sys
from contextvars import ContextVar

from pythonjsonlogger import jsonlogger

# ContextVars pour le suivi des métadonnées de requête
request_id_var: ContextVar[str] = ContextVar("request_id", default="")
user_id_var: ContextVar[str] = ContextVar("user_id", default="")


class RequestIdFilter(logging.Filter):
    """Ajoute request_id et user_id à chaque enregistrement de log."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        record.user_id = user_id_var.get()
        return True


def setup_logging() -> None:
    """Configure le logging structuré en JSON pour l'application."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    # Évite la duplication des handlers
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        handler = logging.StreamHandler(sys.stdout)
        formatter = jsonlogger.JsonFormatter(
            fmt="%(asctime)s %(name)s %(levelname)s %(message)s %(request_id)s %(user_id)s",
            datefmt="%Y-%m-%dT%H:%M:%S",
        )
        handler.setFormatter(formatter)
        handler.addFilter(RequestIdFilter())
        root.addHandler(handler)

    # Réduit le bruit des bibliothèques tierces
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    root.info("Structured JSON logging configured")


def get_logger(name: str) -> logging.Logger:
    """Retourne un logger pour le module donné.

    Args:
        name: Nom du module (généralement __name__).

    Returns:
        Une instance de logging.Logger configurée.
    """
    return logging.getLogger(name)

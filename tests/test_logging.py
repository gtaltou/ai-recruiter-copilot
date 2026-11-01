"""Tests unitaires pour app/core/logging.py."""
import json
import logging
import sys

import pytest

from app.core.logging import StructuredFormatter, setup_logging


class TestStructuredFormatter:
    """Tests du formateur JSON structuré."""

    def _make_record(self, **kwargs) -> logging.LogRecord:
        return logging.LogRecord(
            name=kwargs.get("name", "test_logger"),
            level=kwargs.get("level", logging.INFO),
            pathname=kwargs.get("pathname", __file__),
            lineno=kwargs.get("lineno", 42),
            msg=kwargs.get("msg", "message de test"),
            args=kwargs.get("args", None),
            exc_info=kwargs.get("exc_info", None),
        )

    def test_format_basic_structure(self):
        """Le JSON contient timestamp, level, logger et message."""
        formatter = StructuredFormatter()
        record = self._make_record(msg="Hello %s", args=("World",))

        output = json.loads(formatter.format(record))

        assert set(output) == {"timestamp", "level", "logger", "message"}
        assert output["level"] == "INFO"
        assert output["logger"] == "test_logger"
        assert output["message"] == "Hello World"
        assert output["timestamp"]  # non vide

    def test_format_with_request_id(self):
        """L'attribut request_id est inclus quand présent."""
        formatter = StructuredFormatter()
        record = self._make_record()
        record.request_id = "req-12345"

        output = json.loads(formatter.format(record))

        assert output["request_id"] == "req-12345"

    def test_format_without_request_id(self):
        """Pas de clé request_id quand l'attribut est absent."""
        formatter = StructuredFormatter()
        record = self._make_record()

        output = json.loads(formatter.format(record))

        assert "request_id" not in output

    def test_format_with_exception(self):
        """La clé exception contient la trace quand exc_info est fourni."""
        formatter = StructuredFormatter()
        try:
            raise ValueError("boom")
        except ValueError:
            exc_info = sys.exc_info()

        record = self._make_record(exc_info=exc_info)
        output = json.loads(formatter.format(record))

        assert "exception" in output
        assert "ValueError" in output["exception"]

    def test_format_unicode_preserved(self):
        """ensure_ascii=False conserve les caractères accentués."""
        formatter = StructuredFormatter()
        record = self._make_record(msg="héllo wörld")

        raw = formatter.format(record)

        assert "héllo wörld" in raw
        assert "\\u00e9" not in raw


class TestSetupLogging:
    """Tests de configuration du logging global."""

    @pytest.fixture(autouse=True)
    def _reset_root_logger(self):
        root = logging.getLogger()
        original_handlers = root.handlers[:]
        original_level = root.level
        root.handlers.clear()
        yield
        root.handlers.clear()
        root.handlers.extend(original_handlers)
        root.setLevel(original_level)

    def test_json_mode_uses_structured_formatter(self):
        """Avec log_json=True, le handler utilise StructuredFormatter."""
        setup_logging(log_json=True)

        root = logging.getLogger()
        assert root.level == logging.INFO
        assert len(root.handlers) == 1
        assert isinstance(root.handlers[0].formatter, StructuredFormatter)

    def test_text_mode_uses_standard_formatter(self):
        """Sans log_json, le formatter est le logging.Formatter classique."""
        setup_logging(log_json=False)

        handler = logging.getLogger().handlers[0]
        assert isinstance(handler.formatter, logging.Formatter)
        assert not isinstance(handler.formatter, StructuredFormatter)

    def test_custom_log_level(self):
        """log_level='DEBUG' règle le niveau du logger racine."""
        setup_logging(log_level="DEBUG")

        assert logging.getLogger().level == logging.DEBUG

    def test_invalid_log_level_falls_back_to_info(self):
        """Un niveau invalide retombe sur INFO."""
        setup_logging(log_level="NOT_A_LEVEL")

        assert logging.getLogger().level == logging.INFO

    def test_handlers_are_cleared_no_duplicates(self):
        """Appeler setup_logging deux fois ne crée pas de doublons."""
        setup_logging()
        setup_logging()

        root = logging.getLogger()
        assert len(root.handlers) == 1

    def test_stream_handler_writes_to_stdout(self):
        """Le handler écrit sur sys.stdout."""
        setup_logging()

        handler = logging.getLogger().handlers[0]
        assert isinstance(handler, logging.StreamHandler)
        assert handler.stream is sys.stdout

    def test_noisy_libs_set_to_warning(self):
        """httpx, httpcore, urllib3 et chromadb passent en WARNING."""
        setup_logging()

        for lib in ("httpx", "httpcore", "urllib3", "chromadb"):
            assert logging.getLogger(lib).level == logging.WARNING

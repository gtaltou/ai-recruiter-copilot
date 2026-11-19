"""Tests pour app/core/logging_config.py"""

import logging
import json
import io
import sys
import uuid

import pytest

from app.core.logging_config import (
    setup_logging,
    get_logger,
    RequestIdFilter,
    request_id_var,
    user_id_var,
)

from app.core.logging_config import request_id_var, user_id_var


class TestRequestIdFilter:
    def test_adds_request_id(self):
        filter_ = RequestIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        request_id_var.set("req-123")
        filter_.filter(record)
        assert record.request_id == "req-123"

    def test_adds_user_id(self):
        filter_ = RequestIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        user_id_var.set("user-456")
        filter_.filter(record)
        assert record.user_id == "user-456"

    def test_default_empty_string(self):
        request_id_var.set("")
        user_id_var.set("")
    
        filter_ = RequestIdFilter()
        record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg="test message",
        args=(),
        exc_info=None,
    )
        filter_.filter(record)
        assert record.request_id == ""
        assert record.user_id == ""

    def test_filter_always_returns_true(self):
        """Le filtre ne doit jamais filtrer un enregistrement."""
        filter_ = RequestIdFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="test message",
            args=(),
            exc_info=None,
        )
        assert filter_.filter(record) is True


class TestSetupLogging:
    def test_sets_root_logger_level(self):
        # Reset
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()
        old_level = root.level

        try:
            setup_logging()
            assert root.level == logging.INFO
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)
            root.setLevel(old_level)

    def test_adds_handler_to_root(self):
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            assert len(root.handlers) == 1
            assert isinstance(root.handlers[0], logging.StreamHandler)
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)

    def test_does_not_duplicate_handlers(self):
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            setup_logging()  # deuxième appel
            assert len(root.handlers) == 1
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)

    def test_json_output_format(self):
        """Vérifie que le handler produit du JSON."""
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            # Capture la sortie
            stream = io.StringIO()
            handler = logging.StreamHandler(stream)
            handler.setFormatter(root.handlers[0].formatter)
            handler.addFilter(RequestIdFilter())
            root.addHandler(handler)

            logger = logging.getLogger("test_json")
            request_id_var.set("req-abc")
            logger.info("Hello %s", "world")

            output = stream.getvalue()
            parsed = json.loads(output)
            assert parsed["message"] == "Hello world"
            assert parsed["levelname"] == "INFO"
            assert parsed["name"] == "test_json"
            assert parsed["request_id"] == "req-abc"
            assert "asctime" in parsed
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)

    def test_sets_third_party_loggers_to_warning(self):
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            assert logging.getLogger("uvicorn.access").level == logging.WARNING
            assert logging.getLogger("httpx").level == logging.WARNING
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)

    def test_startup_log_message(self, capsys):
        """Vérifie que le message de démarrage est émis."""
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            captured = capsys.readouterr()
            assert "Structured JSON logging configured" in captured.out
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)


class TestGetLogger:
    def test_returns_logger_with_name(self):
        logger = get_logger("my.module")
        assert logger.name == "my.module"
        assert isinstance(logger, logging.Logger)

    def test_returns_same_logger(self):
        logger1 = get_logger("test.same")
        logger2 = get_logger("test.same")
        assert logger1 is logger2

    def test_inherits_root_config(self):
        root = logging.getLogger()
        old_handlers = root.handlers.copy()
        root.handlers.clear()

        try:
            setup_logging()
            logger = get_logger("test.inherit")
            assert logger.getEffectiveLevel() == logging.INFO
        finally:
            root.handlers.clear()
            root.handlers.extend(old_handlers)

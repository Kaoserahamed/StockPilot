"""Structured logging configuration for StockPilot backend.

Uses python-json-logger to emit JSON lines that Azure Log Analytics,
Docker, and any ELK/Splunk-style collector can ingest without parsing.
"""
import logging
import sys
from typing import Any

try:
    from pythonjsonlogger import jsonlogger  # type: ignore
    _HAS_JSON = True
except ImportError:
    _HAS_JSON = False


class _ExtraFilter(logging.Filter):
    """Attach default extra fields so every log line carries context."""

    def __init__(self, app_name: str = "stockpilot"):
        super().__init__()
        self.app_name = app_name

    def filter(self, record: logging.LogRecord) -> bool:
        record.app = self.app_name  # type: ignore[attr-defined]
        return True


def setup_logging(level: str = "INFO", json_format: bool = True) -> None:
    """Configure root logger for the application.

    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        json_format: If True and python-json-logger is installed, emit JSON.
                     Falls back to coloured text otherwise.
    """
    root = logging.getLogger()
    root.setLevel(level.upper())

    # Clear existing handlers to avoid duplicates on reload.
    for h in list(root.handlers):
        root.removeHandler(h)

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(_ExtraFilter())

    if json_format and _HAS_JSON:
        fmt = "%(asctime)s %(levelname)s %(name)s %(message)s %(app)s"
        formatter = jsonlogger.Jsonfmt(fmt, datefmt="%Y-%m-%dT%H:%M:%S%z")
    else:
        fmt = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s"
        formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet noisy third-party loggers in production.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger with the standard configuration applied."""
    return logging.getLogger(name)

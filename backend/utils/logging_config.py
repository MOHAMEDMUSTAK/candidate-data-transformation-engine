from __future__ import annotations

"""
Eightfold AI - Logging Configuration

Configures structured logging for the application.
Supports both JSON and text output formats.
"""

import logging
import sys
from datetime import datetime

from backend.config import settings


class StructuredFormatter(logging.Formatter):
    """Custom formatter producing structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.utcnow().isoformat() + "Z"
        level = record.levelname
        module = record.module
        message = record.getMessage()

        if settings.log_format == "json":
            import json
            return json.dumps({
                "timestamp": timestamp,
                "level": level,
                "module": module,
                "message": message,
            })
        else:
            return f"[{timestamp}] {level:8s} | {module:20s} | {message}"


def setup_logging() -> None:
    """Configure application-wide logging."""
    root = logging.getLogger()
    root.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))

    # Clear existing handlers
    root.handlers = []

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(StructuredFormatter())
    root.addHandler(handler)

    # Suppress noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)

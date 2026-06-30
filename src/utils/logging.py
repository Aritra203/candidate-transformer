"""Structured logging configuration for the candidate transformer pipeline.

Provides a single `get_logger` factory that returns stdlib loggers configured
with a consistent format. Verbose mode is toggled once at startup via
`configure_logging`.

Design decision: stdlib logging over structlog/loguru to avoid adding
dependencies for a concern this simple. The format includes timestamps,
level, and module name — sufficient for debugging without noise.
"""

from __future__ import annotations

import logging
import sys
from typing import Final

_LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
_DATE_FORMAT: Final[str] = "%Y-%m-%dT%H:%M:%S"

_configured: bool = False


def configure_logging(*, verbose: bool = False) -> None:
    """Configure root logger for the pipeline.

    Call once at CLI entry point. Subsequent calls are no-ops.

    Args:
        verbose: If True, set level to DEBUG. Otherwise INFO.
    """
    global _configured
    if _configured:
        return

    level = logging.DEBUG if verbose else logging.INFO
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT))

    root = logging.getLogger("candidate_transformer")
    root.setLevel(level)
    root.addHandler(handler)
    # Prevent duplicate handlers if stdlib root is also configured.
    root.propagate = False

    _configured = True


def get_logger(name: str) -> logging.Logger:
    """Return a logger namespaced under the pipeline root.

    Args:
        name: Typically ``__name__`` of the calling module.

    Returns:
        A configured ``logging.Logger`` instance.
    """
    return logging.getLogger(f"candidate_transformer.{name}")

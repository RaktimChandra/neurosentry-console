"""Structured logging configuration.

Replaces the ad-hoc print()s scattered across the codebase with a proper logger
hierarchy so logs are grep-able in production (Railway/Render pipe stdout to
their log aggregator automatically).
"""
from __future__ import annotations

import logging
import sys
from typing import Literal


LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class _ColorFormatter(logging.Formatter):
    """Human-readable formatter with ANSI colours for TTYs."""

    _COLORS = {
        logging.DEBUG:    "\033[36m",   # cyan
        logging.INFO:     "\033[32m",   # green
        logging.WARNING:  "\033[33m",   # yellow
        logging.ERROR:    "\033[31m",   # red
        logging.CRITICAL: "\033[41m",   # red bg
    }
    _RESET = "\033[0m"

    def __init__(self, use_color: bool) -> None:
        super().__init__(
            fmt="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
            datefmt="%H:%M:%S",
        )
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        if not self.use_color:
            return base
        colour = self._COLORS.get(record.levelno, "")
        return f"{colour}{base}{self._RESET}"


def configure_logging(level: LogLevel = "INFO") -> None:
    """Set up the root logger once at app startup."""
    root = logging.getLogger()
    if root.handlers:            # already configured
        return
    root.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(_ColorFormatter(use_color=sys.stdout.isatty()))
    root.addHandler(handler)
    # Quiet the noisier third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a namespaced logger (prefer `neurosentry.<module>` names)."""
    if not name.startswith("neurosentry."):
        name = f"neurosentry.{name}"
    return logging.getLogger(name)

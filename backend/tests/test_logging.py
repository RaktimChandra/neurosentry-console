"""Tests for the logging configuration."""
import logging

from app.core.logging_config import configure_logging, get_logger


def test_configure_logging_is_idempotent():
    """Calling twice should not create duplicate handlers."""
    configure_logging("INFO")
    n1 = len(logging.getLogger().handlers)
    configure_logging("INFO")
    n2 = len(logging.getLogger().handlers)
    assert n1 == n2


def test_get_logger_namespacing():
    log = get_logger("myservice")
    assert log.name == "neurosentry.myservice"


def test_get_logger_respects_existing_prefix():
    log = get_logger("neurosentry.alreadyprefixed")
    assert log.name == "neurosentry.alreadyprefixed"

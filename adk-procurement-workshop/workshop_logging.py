"""Quiet console defaults for workshop demos (imported by each agent package)."""

from __future__ import annotations

import logging
import os
import warnings

_CONFIGURED = False

# Loggers that are noisy at INFO/WARNING during adk web runs.
_QUIET_LOGGER_NAMES = (
    "google_adk",
    "google.adk",
    "google.genai",
    "httpx",
    "httpcore",
    "urllib3",
)


def configure_quiet_console(
    log_level: str | None = None,
    *,
    suppress_python_warnings: bool = True,
) -> None:
    """Reduce ADK/HTTP chatter and Python warnings in the terminal.

    Level defaults to WORKSHOP_LOG_LEVEL env var, then ERROR.
    """
    global _CONFIGURED
    if _CONFIGURED:
        return
    _CONFIGURED = True

    if suppress_python_warnings:
        warnings.filterwarnings("ignore")

    level_name = (log_level or os.environ.get("WORKSHOP_LOG_LEVEL") or "ERROR").upper()
    level = getattr(logging, level_name, logging.ERROR)

    try:
        from google.adk.cli.utils import logs as adk_logs

        adk_logs.setup_adk_logger(level)
    except ImportError:
        logging.basicConfig(level=level, force=True)

    for name in _QUIET_LOGGER_NAMES:
        logging.getLogger(name).setLevel(level)

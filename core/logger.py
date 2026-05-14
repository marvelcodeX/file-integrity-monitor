"""
core/logger.py
Tamper-evident, timestamped log writer.
Each log line is written with an HMAC signature derived from a session key,
making post-hoc modification detectable.
"""

import logging
import hmac
import hashlib
import os
import secrets
from datetime import datetime
from pathlib import Path

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
LOG_FILE = os.path.join(LOG_DIR, "fim.log")

# Session key generated at startup — logs signed with this key
_SESSION_KEY: bytes = secrets.token_bytes(32)


def _sign(message: str) -> str:
    """Return a short HMAC-SHA256 hex tag for a log message."""
    sig = hmac.new(_SESSION_KEY, message.encode(), hashlib.sha256)
    return sig.hexdigest()[:16]


class _TamperEvidentFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = super().format(record)
        tag = _sign(base)
        return f"{base} [sig:{tag}]"


def get_logger(name: str = "FIM") -> logging.Logger:
    """
    Return a logger that writes tamper-evident lines to fim.log
    and also echoes to the console.
    """
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger  # Already configured

    logger.setLevel(logging.DEBUG)

    fmt = _TamperEvidentFormatter(
        fmt="%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # File handler
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    # Console handler (plain, no signature)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(levelname)-8s | %(message)s"))
    logger.addHandler(ch)

    return logger


# ── Convenience helpers ───────────────────────────────────────────────────────

_logger = get_logger()


def log_baseline_created(directory: str, file_count: int) -> None:
    _logger.info(f"BASELINE CREATED | dir={directory!r} | files={file_count}")


def log_alert(event_type: str, filepath: str, detail: str = "") -> None:
    msg = f"ALERT | event={event_type} | file={filepath!r}"
    if detail:
        msg += f" | {detail}"
    _logger.warning(msg)


def log_monitor_started(directory: str) -> None:
    _logger.info(f"MONITOR STARTED  | dir={directory!r}")


def log_monitor_stopped(directory: str) -> None:
    _logger.info(f"MONITOR STOPPED  | dir={directory!r}")


def log_info(message: str) -> None:
    _logger.info(message)


def log_error(message: str) -> None:
    _logger.error(message)
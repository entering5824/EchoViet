"""Centralized logging configuration."""
import logging
import sys
from pathlib import Path
from typing import Optional

_default_log_level = "INFO"
_default_log_file: Optional[str] = None


def get_logger(name: str, level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """Get or create a logger with optional level and file output."""
    log = logging.getLogger(name)
    if level is None:
        level = _default_log_level
    if log_file is None:
        log_file = _default_log_file

    if not log.handlers:
        log.setLevel(getattr(logging, level.upper(), logging.INFO))
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        h = logging.StreamHandler(sys.stdout)
        h.setFormatter(fmt)
        log.addHandler(h)
        if log_file:
            try:
                fh = logging.FileHandler(log_file, encoding="utf-8")
                fh.setFormatter(fmt)
                log.addHandler(fh)
            except Exception:
                pass
    return log


def configure_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Set default logging level and optional log file for all loggers created via get_logger."""
    global _default_log_level, _default_log_file
    _default_log_level = level
    _default_log_file = log_file

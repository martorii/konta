import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()

_ENV_VAR = "LOG_LEVEL"

_LEVEL_COLORS = {
    logging.DEBUG: "\033[36m",  # cyan
    logging.INFO: "\033[32m",  # green
    logging.WARNING: "\033[33m",  # yellow
    logging.ERROR: "\033[31m",  # red
    logging.CRITICAL: "\033[1;31m",  # bold red
}
_RESET = "\033[0m"


class _ColorFormatter(logging.Formatter):
    """Formats log records with a color per level for console output."""

    def format(self, record: logging.LogRecord) -> str:
        color = _LEVEL_COLORS.get(record.levelno, _RESET)
        message = super().format(record)
        return f"{color}{message}{_RESET}"


def _resolve_level(level: int | None) -> int:
    if level is not None:
        return level

    env_value = os.environ.get(_ENV_VAR)
    if not env_value:
        return logging.INFO

    resolved = logging.getLevelNamesMapping().get(env_value.upper())
    if resolved is None:
        raise ValueError(f"Invalid {_ENV_VAR} value: {env_value!r}")

    return resolved


def get_logger(name: str = "konta", level: int | None = None) -> logging.Logger:
    """Returns a console logger with colored output per level, configured once per name.

    Level defaults to the `LOG_LEVEL` env var (loaded from `.env`), falling back to INFO.
    """

    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(_ColorFormatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))

    logger.addHandler(handler)
    logger.setLevel(_resolve_level(level))
    logger.propagate = False

    return logger

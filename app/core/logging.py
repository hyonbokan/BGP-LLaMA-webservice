import logging
from logging.config import dictConfig

from app.core.config import get_settings

_LOG_FORMAT = "%(asctime)s %(levelname)-8s %(name)s: %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging() -> None:
    """Configure logging once, at app startup. Level comes from LOG_LEVEL."""
    level = get_settings().log_level.upper()
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {"format": _LOG_FORMAT, "datefmt": _DATE_FORMAT},
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "default",
                    "stream": "ext://sys.stdout",
                },
            },
            # Third-party loggers (openai, httpx, …) propagate to root.
            "root": {"handlers": ["console"], "level": level},
            "loggers": {
                # Our code and the servers share one format; propagate=False
                # keeps each message to a single handler (no double logging).
                "app": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
                "uvicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
                "gunicorn.error": {"handlers": ["console"], "level": level, "propagate": False},
                "gunicorn.access": {"handlers": ["console"], "level": level, "propagate": False},
            },
        }
    )


def get_logger(name: str) -> logging.Logger:
    """Module logger. Use as: ``logger = get_logger(__name__)``."""
    return logging.getLogger(name)

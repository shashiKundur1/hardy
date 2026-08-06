import logging
import sys
from logging.config import dictConfig

from src.config import settings

ROOT_LOGGER = "hardy"
SERVER_LOGGERS = (
    "hypercorn.error",
    "hypercorn.access",
    "uvicorn.error",
    "uvicorn.access",
)


def configure_logging() -> None:
    level = settings.log_level.upper()
    server = {
        name: {"handlers": ["console"], "level": level, "propagate": False}
        for name in SERVER_LOGGERS
    }
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "console": {
                    "format": "%(asctime)s %(levelname)-8s %(name)s %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "stream": sys.stdout,
                    "formatter": "console",
                }
            },
            "loggers": {
                ROOT_LOGGER: {
                    "handlers": ["console"],
                    "level": level,
                    "propagate": False,
                },
                **server,
            },
            "root": {"handlers": ["console"], "level": "WARNING"},
        }
    )


def get_logger(name: str | None = None) -> logging.Logger:
    return logging.getLogger(ROOT_LOGGER if name is None else f"{ROOT_LOGGER}.{name}")

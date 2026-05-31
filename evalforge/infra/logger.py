import logging

import structlog
from structlog.types import BoundLogger


def configure_logging(app_env: str) -> None:
    renderer = (
        structlog.processors.JSONRenderer()
        if app_env == "production"
        else structlog.dev.ConsoleRenderer(colors=True)
    )

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            renderer,
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    logging.basicConfig(
        format="%(message)s",
        level=logging.DEBUG if app_env != "production" else logging.INFO,
    )


def get_logger(name: str) -> BoundLogger:
    return structlog.get_logger(name)

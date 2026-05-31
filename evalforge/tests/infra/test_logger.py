import structlog

from infra.logger import configure_logging, get_logger


def test_logger_returns_bound_logger():
    logger = get_logger("test")
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "error")
    assert hasattr(logger, "warning")


def test_configure_logging_runs_without_error_in_development():
    configure_logging(app_env="development")


def test_configure_logging_runs_without_error_in_production():
    configure_logging(app_env="production")


def test_log_contains_required_fields():
    captured = []

    def list_processor(logger, method, event_dict):
        captured.append(event_dict.copy())
        raise structlog.DropEvent()

    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            list_processor,
        ],
        wrapper_class=structlog.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
    )

    logger = get_logger("test_log_fields")
    logger.info("test_event", key="value")

    assert len(captured) == 1
    entry = captured[0]
    assert "event" in entry
    assert "level" in entry
    assert "logger" in entry
    assert "timestamp" in entry

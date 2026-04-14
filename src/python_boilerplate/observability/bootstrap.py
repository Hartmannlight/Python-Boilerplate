from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from opentelemetry import trace
from structlog.stdlib import BoundLogger

from python_boilerplate.config import Settings
from python_boilerplate.observability.errors import (
    configure_error_tracking,
    flush_error_tracking,
)
from python_boilerplate.observability.logging import configure_logging, get_logger
from python_boilerplate.observability.metrics import Metrics
from python_boilerplate.observability.tracing import configure_tracing, shutdown_tracing


@dataclass(slots=True, frozen=True)
class ObservabilityRuntime:
    logger: BoundLogger
    metrics: Metrics
    tracer: trace.Tracer
    shutdown: Callable[[], None]


def setup_observability(settings: Settings, logger_name: str) -> ObservabilityRuntime:
    configure_logging(settings)
    configure_error_tracking(settings)
    tracer = configure_tracing(settings)
    metrics = Metrics(settings)
    metrics.start()
    logger = get_logger(settings, logger_name)
    return ObservabilityRuntime(
        logger=logger,
        metrics=metrics,
        tracer=tracer,
        shutdown=_shutdown_observability,
    )


def _shutdown_observability() -> None:
    shutdown_tracing()
    flush_error_tracking()

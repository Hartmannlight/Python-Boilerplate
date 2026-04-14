from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any, cast

import structlog
from opentelemetry import trace

from python_boilerplate.config import Settings


def _rename_event_key(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    event_dict["msg"] = event_dict["event"]
    return event_dict


def _add_trace_context(
    _: Any, __: str, event_dict: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    span = trace.get_current_span()
    span_context = span.get_span_context()
    if span_context.is_valid:
        event_dict["trace_id"] = f"{span_context.trace_id:032x}"
        event_dict["span_id"] = f"{span_context.span_id:016x}"
    return event_dict


def configure_logging(settings: Settings) -> None:
    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True, key="ts")

    logging.basicConfig(
        format="%(message)s",
        level=getattr(logging, settings.log_level, logging.INFO),
        stream=sys.stdout,
    )

    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            timestamper,
            _add_trace_context,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            _rename_event_key,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(settings: Settings, logger_name: str) -> structlog.stdlib.BoundLogger:
    logger = structlog.get_logger(logger_name)
    return cast(
        structlog.stdlib.BoundLogger,
        logger.bind(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            instance=settings.instance,
        ),
    )

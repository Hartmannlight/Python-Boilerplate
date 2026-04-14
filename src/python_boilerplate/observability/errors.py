from __future__ import annotations

from sentry_sdk import capture_exception, flush, init

from python_boilerplate.config import Settings


def configure_error_tracking(settings: Settings) -> None:
    if not settings.sentry_dsn:
        return
    init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=f"{settings.service_name}@{settings.version}",
        traces_sample_rate=settings.traces_sample_rate if settings.traces_enabled else 0.0,
    )


def report_exception(exc: BaseException) -> None:
    capture_exception(exc)


def flush_error_tracking(timeout_seconds: float = 2.0) -> None:
    flush(timeout=timeout_seconds)

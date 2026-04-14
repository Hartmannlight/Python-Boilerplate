from __future__ import annotations

from typing import Any, cast

import pytest

from python_boilerplate.config import Settings
from python_boilerplate.observability import logging as app_logging
from python_boilerplate.observability import metrics as app_metrics
from python_boilerplate.observability import tracing
from python_boilerplate.observability.bootstrap import ObservabilityRuntime
from python_boilerplate.services.worker import WorkerService


def test_configure_tracing_reuses_provider_for_matching_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_instances: list[object] = []
    set_calls: list[object] = []
    get_tracer_calls: list[str] = []
    trace_api = cast(Any, tracing).trace

    class ProviderStub:
        def __init__(self, resource: object, sampler: object) -> None:
            self.resource = resource
            self.sampler = sampler
            self.processors: list[object] = []
            provider_instances.append(self)

        def add_span_processor(self, processor: object) -> None:
            self.processors.append(processor)

    monkeypatch.setattr(tracing, "_TRACER_PROVIDER_OWNER", None)
    monkeypatch.setattr(tracing, "TracerProvider", ProviderStub)

    def set_tracer_provider_stub(provider: object) -> None:
        set_calls.append(provider)

    def get_tracer_stub(name: str) -> Any:
        get_tracer_calls.append(name)
        return object()

    monkeypatch.setattr(trace_api, "set_tracer_provider", set_tracer_provider_stub)
    monkeypatch.setattr(
        trace_api,
        "get_tracer",
        get_tracer_stub,
    )

    first = tracing.configure_tracing(
        Settings(service_name="svc-a", version="1.0.0", environment="test")
    )
    second = tracing.configure_tracing(
        Settings(service_name="svc-a", version="1.0.0", environment="test")
    )

    assert first is not None
    assert second is not None
    assert len(provider_instances) == 1
    assert set_calls == [provider_instances[0]]
    assert get_tracer_calls == ["svc-a", "svc-a"]


def test_configure_tracing_configures_ratio_sampler(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider_instances: list[Any] = []
    trace_api = cast(Any, tracing).trace

    class ProviderStub:
        def __init__(self, resource: object, sampler: object) -> None:
            self.resource = resource
            self.sampler = sampler
            provider_instances.append(self)

        def add_span_processor(self, _processor: object) -> None:
            return None

    monkeypatch.setattr(tracing, "_TRACER_PROVIDER_OWNER", None)
    monkeypatch.setattr(tracing, "TracerProvider", ProviderStub)
    monkeypatch.setattr(trace_api, "set_tracer_provider", lambda _provider: None)
    monkeypatch.setattr(trace_api, "get_tracer", lambda _name: object())

    tracing.configure_tracing(
        Settings(
            service_name="svc-a",
            version="1.0.0",
            environment="test",
            traces_enabled=True,
            traces_sample_rate=0.25,
        )
    )

    assert len(provider_instances) == 1
    sampler_description = provider_instances[0].sampler.get_description()
    assert "TraceIdRatioBased{0.25}" in sampler_description


def test_configure_tracing_rejects_conflicting_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    trace_api = cast(Any, tracing).trace
    provider_instances: list[object] = []
    set_calls: list[object] = []
    get_tracer_calls: list[str] = []

    class ProviderStub:
        def __init__(self, resource: object, sampler: object) -> None:
            self.resource = resource
            self.sampler = sampler
            provider_instances.append(self)

        def add_span_processor(self, _processor: object) -> None:
            return None

    monkeypatch.setattr(tracing, "_TRACER_PROVIDER_OWNER", None)
    monkeypatch.setattr(tracing, "TracerProvider", ProviderStub)

    def set_tracer_provider_stub(provider: object) -> None:
        set_calls.append(provider)

    def get_tracer_stub(name: str) -> Any:
        get_tracer_calls.append(name)
        return object()

    monkeypatch.setattr(trace_api, "set_tracer_provider", set_tracer_provider_stub)
    monkeypatch.setattr(trace_api, "get_tracer", get_tracer_stub)

    tracing.configure_tracing(Settings(service_name="svc-a", version="1.0.0", environment="test"))
    with pytest.raises(RuntimeError, match="Tracing is already configured"):
        tracing.configure_tracing(
            Settings(service_name="svc-b", version="2.0.0", environment="prod")
        )

    assert len(provider_instances) == 1
    assert set_calls == [provider_instances[0]]
    assert get_tracer_calls == ["svc-a"]


def test_metrics_mark_failure_updates_progress_timestamp() -> None:
    metrics = app_metrics.Metrics(Settings())

    app_metrics_time = cast(Any, app_metrics).time
    original_time = app_metrics_time
    try:
        cast(Any, app_metrics).time = lambda: 123.0
        metrics.mark_failure(0.5)
    finally:
        cast(Any, app_metrics).time = original_time

    assert metrics.last_progress_timestamp_seconds._value.get() == 123.0
    assert metrics.failures_total._value.get() == 1.0


def test_worker_reports_exception_once_at_process_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    reported: list[BaseException] = []
    warnings: list[tuple[str, dict[str, object]]] = []
    exceptions: list[tuple[str, dict[str, object]]] = []
    shutdown_calls: list[str] = []
    runtime_shutdown_calls: list[str] = []

    class LoggerStub:
        def bind(self, **_kwargs: object) -> LoggerStub:
            return self

        def info(self, *_args: object, **_kwargs: object) -> None:
            return None

        def warning(self, event: str, **kwargs: object) -> None:
            warnings.append((event, kwargs))

        def exception(self, event: str, **kwargs: object) -> None:
            exceptions.append((event, kwargs))

    class MetricsStub:
        def mark_failure(self, _duration_seconds: float) -> None:
            return None

        def mark_shutdown(self) -> None:
            shutdown_calls.append("shutdown")

    class SpanContextStub:
        def __enter__(self) -> SpanContextStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def set_attribute(self, _key: str, _value: str) -> None:
            return None

    class TracerStub:
        def start_as_current_span(self, _name: str) -> SpanContextStub:
            return SpanContextStub()

    class FailingWorkerService(WorkerService):
        def install_signal_handlers(self) -> None:
            return None

        def execute_iteration(self, _stop_event: object) -> None:
            raise RuntimeError("boom")

    runtime = cast(
        ObservabilityRuntime,
        type(
            "RuntimeStub",
            (),
            {
                "logger": LoggerStub(),
                "metrics": MetricsStub(),
                "tracer": TracerStub(),
                "shutdown": staticmethod(lambda: runtime_shutdown_calls.append("runtime")),
            },
        )(),
    )
    service = FailingWorkerService(settings=Settings(), runtime=runtime)

    monkeypatch.setattr("python_boilerplate.services.worker.report_exception", reported.append)

    exit_code = service.run()

    assert exit_code == 1
    assert len(reported) == 1
    assert isinstance(reported[0], RuntimeError)
    assert warnings == [
        (
            "iteration_failed",
            {
                "outcome": "failure",
                "error": "boom",
                "exception_type": "RuntimeError",
            },
        )
    ]
    assert [event for event, _kwargs in exceptions] == ["crashed"]
    assert shutdown_calls == ["shutdown"]
    assert runtime_shutdown_calls == ["runtime"]


def test_worker_flushes_observability_on_clean_shutdown() -> None:
    shutdown_calls: list[str] = []
    runtime_shutdown_calls: list[str] = []
    info_events: list[str] = []

    class LoggerStub:
        def bind(self, **_kwargs: object) -> LoggerStub:
            return self

        def info(self, event: str, **_kwargs: object) -> None:
            info_events.append(event)

    class MetricsStub:
        def mark_shutdown(self) -> None:
            shutdown_calls.append("shutdown")

    class ServiceStub(WorkerService):
        def install_signal_handlers(self) -> None:
            return None

        def run_iteration(self) -> None:
            self.stop_event.set()

    runtime = cast(
        ObservabilityRuntime,
        type(
            "RuntimeStub",
            (),
            {
                "logger": LoggerStub(),
                "metrics": MetricsStub(),
                "tracer": object(),
                "shutdown": staticmethod(lambda: runtime_shutdown_calls.append("runtime")),
            },
        )(),
    )
    service = ServiceStub(settings=Settings(), runtime=runtime)

    exit_code = service.run()

    assert exit_code == 0
    assert shutdown_calls == ["shutdown"]
    assert runtime_shutdown_calls == ["runtime"]
    assert info_events == ["startup_success", "shutdown_complete"]


def test_worker_passes_stop_event_into_iteration() -> None:
    received_stop_events: list[object] = []

    class LoggerStub:
        def bind(self, **_kwargs: object) -> LoggerStub:
            return self

        def info(self, *_args: object, **_kwargs: object) -> None:
            return None

        def warning(self, *_args: object, **_kwargs: object) -> None:
            return None

    class MetricsStub:
        def mark_success(self, _duration_seconds: float) -> None:
            return None

    class SpanContextStub:
        def __enter__(self) -> SpanContextStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def set_attribute(self, _key: str, _value: str) -> None:
            return None

    class TracerStub:
        def start_as_current_span(self, _name: str) -> SpanContextStub:
            return SpanContextStub()

    class ServiceStub(WorkerService):
        def execute_iteration(self, stop_event: object) -> None:
            received_stop_events.append(stop_event)

    runtime = cast(
        ObservabilityRuntime,
        type(
            "RuntimeStub",
            (),
            {
                "logger": LoggerStub(),
                "metrics": MetricsStub(),
                "tracer": TracerStub(),
                "shutdown": staticmethod(lambda: None),
            },
        )(),
    )

    service = ServiceStub(settings=Settings(), runtime=runtime)

    service.run_iteration()

    assert received_stop_events == [service.stop_event]


def test_shutdown_observability_flushes_tracing_before_error_tracking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from python_boilerplate.observability import bootstrap

    calls: list[str] = []
    monkeypatch.setattr(bootstrap, "shutdown_tracing", lambda: calls.append("tracing"))
    monkeypatch.setattr(bootstrap, "flush_error_tracking", lambda: calls.append("errors"))

    bootstrap._shutdown_observability()

    assert calls == ["tracing", "errors"]


def test_logging_adds_trace_context_when_span_is_active(monkeypatch: pytest.MonkeyPatch) -> None:
    class SpanContextStub:
        is_valid = True
        trace_id = int("1234", 16)
        span_id = int("abcd", 16)

    class SpanStub:
        def get_span_context(self) -> SpanContextStub:
            return SpanContextStub()

    trace_api = cast(Any, app_logging).trace
    monkeypatch.setattr(trace_api, "get_current_span", lambda: SpanStub())

    event_dict = app_logging._add_trace_context(None, "info", {"event": "test"})

    assert event_dict["trace_id"] == "00000000000000000000000000001234"
    assert event_dict["span_id"] == "000000000000abcd"

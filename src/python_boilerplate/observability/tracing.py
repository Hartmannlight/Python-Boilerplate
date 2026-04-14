from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider, sampling
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from python_boilerplate.config import Settings

_TRACER_PROVIDER_LOCK = Lock()
_TRACER_PROVIDER_OWNER: tuple[str, str, str, str, bool, str, float] | None = None


def configure_tracing(settings: Settings) -> trace.Tracer:
    global _TRACER_PROVIDER_OWNER

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": settings.version,
            "deployment.environment": settings.environment,
            "service.instance.id": settings.instance,
        }
    )

    owner = (
        settings.service_name,
        settings.version,
        settings.environment,
        settings.instance,
        settings.traces_enabled,
        settings.otlp_endpoint,
        settings.traces_sample_rate,
    )
    with _TRACER_PROVIDER_LOCK:
        if _TRACER_PROVIDER_OWNER is None:
            provider = TracerProvider(
                resource=resource,
                sampler=_build_sampler(settings),
            )
            if settings.traces_enabled and settings.otlp_endpoint:
                exporter = OTLPSpanExporter(endpoint=settings.otlp_endpoint)
                provider.add_span_processor(BatchSpanProcessor(exporter))
            trace.set_tracer_provider(provider)
            _TRACER_PROVIDER_OWNER = owner
        elif _TRACER_PROVIDER_OWNER != owner:
            msg = (
                "Tracing is already configured with different settings for this process. "
                "Initialize observability once per process with one stable tracing configuration."
            )
            raise RuntimeError(msg)

    return trace.get_tracer(settings.service_name)


def shutdown_tracing() -> None:
    provider = trace.get_tracer_provider()
    force_flush = getattr(provider, "force_flush", None)
    if callable(force_flush):
        force_flush()
    shutdown = getattr(provider, "shutdown", None)
    if callable(shutdown):
        shutdown()


def _build_sampler(settings: Settings) -> sampling.Sampler:
    if not settings.traces_enabled:
        return sampling.ALWAYS_OFF
    return sampling.ParentBased(sampling.TraceIdRatioBased(settings.traces_sample_rate))


@contextmanager
def root_span(tracer: trace.Tracer, span_name: str, **attributes: str) -> Iterator[None]:
    with tracer.start_as_current_span(span_name) as span:
        for key, value in attributes.items():
            span.set_attribute(key, value)
        yield

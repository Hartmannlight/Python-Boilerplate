from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter, time

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, start_http_server

from python_boilerplate.config import Settings


@dataclass(slots=True)
class Metrics:
    settings: Settings
    registry: CollectorRegistry = field(default_factory=CollectorRegistry)
    app_up: Gauge = field(init=False)
    app_info: Gauge = field(init=False)
    app_start_time_seconds: Gauge = field(init=False)
    last_progress_timestamp_seconds: Gauge = field(init=False)
    iterations_total: Counter = field(init=False)
    iteration_duration_seconds: Histogram = field(init=False)
    last_success_timestamp_seconds: Gauge = field(init=False)
    failures_total: Counter = field(init=False)

    def __post_init__(self) -> None:
        self.app_up = Gauge(
            "app_up",
            "Whether the service is considered healthy.",
            registry=self.registry,
        )
        self.app_info = Gauge(
            "app_info",
            "Static application metadata.",
            labelnames=("version", "commit", "env"),
            registry=self.registry,
        )
        self.app_start_time_seconds = Gauge(
            "app_start_time_seconds",
            "Unix timestamp when the service started.",
            registry=self.registry,
        )
        self.last_progress_timestamp_seconds = Gauge(
            "last_progress_timestamp_seconds",
            "Unix timestamp of the last observed service progress signal.",
            registry=self.registry,
        )
        self.iterations_total = Counter(
            "iterations_total",
            "Total completed service iterations.",
            labelnames=("outcome",),
            registry=self.registry,
        )
        self.iteration_duration_seconds = Histogram(
            "iteration_duration_seconds",
            "Duration of service iterations in seconds.",
            registry=self.registry,
        )
        self.last_success_timestamp_seconds = Gauge(
            "last_success_timestamp_seconds",
            "Unix timestamp of the last successful iteration.",
            registry=self.registry,
        )
        self.failures_total = Counter(
            "failures_total",
            "Total failed service iterations.",
            registry=self.registry,
        )

    def start(self) -> None:
        now = time()
        self.app_up.set(1)
        self.app_info.labels(
            version=self.settings.version,
            commit=self.settings.commit,
            env=self.settings.environment,
        ).set(1)
        self.app_start_time_seconds.set(now)
        self.last_progress_timestamp_seconds.set(now)
        if self.settings.metrics_enabled:
            start_http_server(
                port=self.settings.metrics_port,
                addr=self.settings.metrics_host,
                registry=self.registry,
            )

    def mark_shutdown(self) -> None:
        self.app_up.set(0)

    def mark_progress(self) -> None:
        self.last_progress_timestamp_seconds.set(time())

    def mark_success(self, duration_seconds: float) -> None:
        now = time()
        self.last_progress_timestamp_seconds.set(now)
        self.iterations_total.labels(outcome="success").inc()
        self.iteration_duration_seconds.observe(duration_seconds)
        self.last_success_timestamp_seconds.set(now)

    def mark_failure(self, duration_seconds: float) -> None:
        self.last_progress_timestamp_seconds.set(time())
        self.iterations_total.labels(outcome="failure").inc()
        self.iteration_duration_seconds.observe(duration_seconds)
        self.failures_total.inc()


@dataclass(slots=True)
class IterationTimer:
    metrics: Metrics
    started_at: float = field(default_factory=perf_counter)

    def observe_success(self) -> None:
        self.metrics.mark_success(perf_counter() - self.started_at)

    def observe_failure(self) -> None:
        self.metrics.mark_failure(perf_counter() - self.started_at)


def start_iteration(metrics: Metrics) -> IterationTimer:
    return IterationTimer(metrics=metrics)

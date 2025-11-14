from __future__ import annotations

import logging

from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)

from app.config import AppConfig

log = logging.getLogger(__name__)

app_requests_total = Counter(
    'app_requests_total',
    'Total HTTP requests.',
    ['route', 'method', 'status'],
)

app_request_duration_seconds = Histogram(
    'app_request_duration_seconds',
    'Request latency distribution.',
    ['route', 'method'],
)

app_errors_total = Counter(
    'app_errors_total',
    'Total application errors.',
    ['reason'],
)

app_build_info = Gauge(
    'app_build_info',
    'Deployment identification.',
    ['version', 'commit', 'env'],
)

process_resident_memory_bytes = Gauge(
    'process_resident_memory_bytes',
    'Memory usage of the process.',
)


def start_metrics_server(config: AppConfig) -> None:
    if not config.metrics_enabled:
        log.info('Metrics disabled')
        return

    start_http_server(config.metrics_port)

    app_build_info.labels(
        version=config.version,
        commit=config.commit,
        env=config.env,
    ).set(1)

    log.info('Metrics server started', extra={'metrics_port': config.metrics_port})

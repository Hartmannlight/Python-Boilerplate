from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from time import time
from urllib.error import URLError
from urllib.request import urlopen

from python_boilerplate.config import Settings


def parse_prometheus_text(payload: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    for line in payload.splitlines():
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            msg = f"Invalid Prometheus metric line: {line!r}"
            raise ValueError(msg)
        metric_name, raw_value = parts
        if "{" in metric_name:
            continue
        metrics[metric_name] = float(raw_value)
    return metrics


@dataclass(slots=True, frozen=True)
class HealthReport:
    service: str
    env: str
    version: str
    commit: str
    timestamp: str
    ok: bool
    reason: str


def check_health(settings: Settings) -> HealthReport:
    if not settings.metrics_enabled:
        return HealthReport(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            timestamp=_timestamp(),
            ok=True,
            reason="metrics_disabled",
        )

    try:
        with urlopen(
            f"http://{_health_host(settings.metrics_host)}:{settings.metrics_port}/metrics",
            timeout=2,
        ) as response:
            payload = response.read().decode("utf-8")
    except URLError:
        return HealthReport(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            timestamp=_timestamp(),
            ok=False,
            reason="metrics_unreachable",
        )

    try:
        metrics = parse_prometheus_text(payload)
    except (UnicodeDecodeError, ValueError):
        return HealthReport(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            timestamp=_timestamp(),
            ok=False,
            reason="metrics_invalid",
        )

    app_up = metrics.get("app_up", 0.0)
    if app_up < 1:
        return HealthReport(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            timestamp=_timestamp(),
            ok=False,
            reason="app_down",
        )

    freshness_signal = metrics.get("last_success_timestamp_seconds")
    if freshness_signal is None:
        freshness_signal = metrics.get("last_progress_timestamp_seconds")

    if freshness_signal is None or settings.health_max_age_seconds <= 0:
        return HealthReport(
            service=settings.service_name,
            env=settings.environment,
            version=settings.version,
            commit=settings.commit,
            timestamp=_timestamp(),
            ok=True,
            reason="ok",
        )

    age = time() - freshness_signal
    is_healthy = age <= settings.health_max_age_seconds
    return HealthReport(
        service=settings.service_name,
        env=settings.environment,
        version=settings.version,
        commit=settings.commit,
        timestamp=_timestamp(),
        ok=is_healthy,
        reason="ok" if is_healthy else "stale",
    )


def emit_health_report(report: HealthReport) -> int:
    print(json.dumps(asdict(report), separators=(",", ":")))
    return 0 if report.ok else 1


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()


def _health_host(metrics_host: str) -> str:
    if metrics_host in {"", "0.0.0.0", "::"}:
        return "127.0.0.1"
    return metrics_host

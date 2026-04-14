from __future__ import annotations

from dataclasses import dataclass
from os import getenv

"""Runtime settings loaded exclusively from environment variables.

This boilerplate treats env vars as the single source of truth for
operational configuration. Optional YAML files are intended only for
large, structured feature configuration in concrete projects.
"""


def parse_bool(value: str) -> bool:
    normalized = value.strip().lower()
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}
    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    msg = f"Unsupported boolean value: {value!r}"
    raise ValueError(msg)


def parse_float(value: str) -> float:
    return float(value.strip())


def parse_int(value: str) -> int:
    return int(value.strip())


@dataclass(slots=True, frozen=True)
class Settings:
    service_name: str = "python-boilerplate"
    environment: str = "development"
    version: str = "0.1.0"
    commit: str = "dev"
    instance: str = "local"
    log_level: str = "INFO"
    debug: bool = False
    loop_interval_seconds: float = 5.0
    metrics_enabled: bool = True
    metrics_host: str = "0.0.0.0"
    metrics_port: int = 9000
    health_max_age_seconds: float = 60.0
    sentry_dsn: str = ""
    traces_enabled: bool = True
    otlp_endpoint: str = ""
    traces_sample_rate: float = 1.0


def load_settings() -> Settings:
    """Load runtime settings from environment variables only."""
    return Settings(
        service_name=getenv("APP_NAME", "python-boilerplate"),
        environment=getenv("APP_ENV", "development"),
        version=getenv("APP_VERSION", "0.1.0"),
        commit=getenv("APP_COMMIT", "dev"),
        instance=getenv("APP_INSTANCE", "local"),
        log_level=getenv("APP_LOG_LEVEL", "INFO").upper(),
        debug=parse_bool(getenv("APP_DEBUG", "false")),
        loop_interval_seconds=parse_float(getenv("APP_LOOP_INTERVAL_SECONDS", "5.0")),
        metrics_enabled=parse_bool(getenv("APP_METRICS_ENABLED", "true")),
        metrics_host=getenv("APP_METRICS_HOST", "0.0.0.0"),
        metrics_port=parse_int(getenv("APP_METRICS_PORT", "9000")),
        health_max_age_seconds=parse_float(getenv("APP_HEALTH_MAX_AGE_SECONDS", "60.0")),
        sentry_dsn=getenv("SENTRY_DSN", ""),
        traces_enabled=parse_bool(getenv("APP_TRACES_ENABLED", "true")),
        otlp_endpoint=getenv("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
        traces_sample_rate=parse_float(getenv("APP_TRACES_SAMPLE_RATE", "1.0")),
    )

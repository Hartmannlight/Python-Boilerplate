from __future__ import annotations

import os
import socket
from dataclasses import dataclass, field


@dataclass
class AppConfig:
    service_name: str = os.getenv('APP_SERVICE_NAME', 'python-boilerplate')  # TODO
    env: str = os.getenv('APP_ENV', 'dev')
    log_level: str = os.getenv('LOG_LEVEL', 'INFO')

    version: str = os.getenv('APP_VERSION', '0.0.0')
    commit: str = os.getenv('APP_COMMIT', 'unknown')
    config_source: str | None = os.getenv('APP_CONFIG_SOURCE')

    feature_flags: list[str] = field(
        default_factory=lambda: os.getenv('APP_FEATURE_FLAGS', '').split(',')
        if os.getenv('APP_FEATURE_FLAGS')
        else [],
    )

    metrics_enabled: bool = os.getenv('METRICS_ENABLED', '1') == '1'
    metrics_port: int = int(os.getenv('METRICS_PORT', '8000'))

    http_host: str = os.getenv('APP_HTTP_HOST', '0.0.0.0')
    http_port: int = int(os.getenv('APP_HTTP_PORT', '8000'))

    instance: str = os.getenv('APP_INSTANCE', socket.gethostname())

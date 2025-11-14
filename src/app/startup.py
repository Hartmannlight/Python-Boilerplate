from __future__ import annotations

import logging
import sys

from app.config import AppConfig

log = logging.getLogger('app')


def log_startup_success(config: AppConfig) -> None:
    log.info(
        'Service started successfully',
        extra={
            'event': 'startup_success',
            'version': config.version,
            'commit': config.commit,
            'config_source': config.config_source,
            'feature_flags': config.feature_flags,
        },
    )


def log_startup_failure(
    config: AppConfig,
    error: str,
    dependency: str | None = None,
) -> None:
    extra: dict[str, object] = {
        'event': 'startup_failed',
        'version': config.version,
        'commit': config.commit,
        'error': error,
    }
    if dependency:
        extra['dependency'] = dependency

    log.error('Service failed to start', extra=extra)
    sys.exit(1)

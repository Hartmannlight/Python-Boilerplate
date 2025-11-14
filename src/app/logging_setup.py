from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any

from app.config import AppConfig


class AccessLogFilter(logging.Filter):
    def __init__(self, ignore_paths: Iterable[str]) -> None:
        super().__init__()
        self._ignore_paths = tuple(ignore_paths)

    def filter(self, record: logging.LogRecord) -> bool:
        if record.name != 'uvicorn.access':
            return True

        msg = record.getMessage()

        for path in self._ignore_paths:
            if f'"GET {path} ' in msg or f'"HEAD {path} ' in msg:
                return False

        return True


class JsonFormatter(logging.Formatter):
    def __init__(self, config: AppConfig) -> None:
        super().__init__()
        self._config = config

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'ts': datetime.utcnow().isoformat(timespec='microseconds') + 'Z',
            'level': record.levelname.lower(),
            'service': self._config.service_name,
            'logger': record.name,
            'instance': self._config.instance,
            'env': self._config.env,
            'msg': record.getMessage(),
        }

        for key, value in record.__dict__.items():
            if key.startswith('_'):
                continue
            if key in payload:
                continue
            if key in {
                'args',
                'msg',
                'name',
                'levelno',
                'levelname',
                'created',
                'msecs',
                'relativeCreated',
                'pathname',
                'filename',
                'module',
                'exc_info',
                'exc_text',
                'stack_info',
                'lineno',
                'funcName',
                'thread',
                'threadName',
                'processName',
                'process',
            }:
                continue
            payload[key] = value

        if record.exc_info:
            payload['stack'] = self.formatException(record.exc_info)
            if record.exc_info[0]:
                payload['exception_type'] = record.exc_info[0].__name__

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(config: AppConfig) -> None:
    root = logging.getLogger()
    root.setLevel(config.log_level)

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(config))

    ignore_paths = ['/metrics', '/healthz', '/readyz']
    handler.addFilter(AccessLogFilter(ignore_paths))

    root.handlers.clear()
    root.addHandler(handler)

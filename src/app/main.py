from __future__ import annotations

import logging

import uvicorn
from dotenv import load_dotenv

from app.config import AppConfig
from app.http import create_app
from app.logging_setup import configure_logging
from app.metrics import start_metrics_server
from app.startup import log_startup_failure, log_startup_success


def main() -> None:
    load_dotenv()
    config = AppConfig()
    configure_logging(config)

    log = logging.getLogger('app')

    try:
        start_metrics_server(config)
        app = create_app(config)
        log_startup_success(config)
    except Exception as exc:  # noqa: BLE001
        log.exception('Startup failed')
        log_startup_failure(config, error=str(exc))
        return

    uvicorn.run(
        app,
        host=config.http_host,
        port=config.http_port,
        log_config=None,
    )


if __name__ == '__main__':
    main()

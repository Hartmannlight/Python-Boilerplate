from __future__ import annotations

from python_boilerplate.config import load_settings
from python_boilerplate.observability import setup_observability
from python_boilerplate.services import WorkerService


def create_worker_service() -> WorkerService:
    settings = load_settings()
    runtime = setup_observability(settings, logger_name="python_boilerplate.service")
    return WorkerService(settings=settings, runtime=runtime)

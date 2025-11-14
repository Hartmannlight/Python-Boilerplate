from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from prometheus_client import make_asgi_app

from app.config import AppConfig
from app.metrics import app_request_duration_seconds, app_requests_total


def create_app(config: AppConfig) -> FastAPI:
    app = FastAPI(title=config.service_name)

    @app.middleware('http')
    async def metrics_middleware(
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        start = time.perf_counter()
        response: Response = await call_next(request)
        duration = time.perf_counter() - start

        route = request.url.path
        method = request.method
        status = response.status_code

        app_requests_total.labels(route=route, method=method, status=status).inc()
        app_request_duration_seconds.labels(route=route, method=method).observe(duration)

        return response

    @app.get('/healthz')
    async def healthz() -> dict[str, str]:
        return {'status': 'ok'}

    @app.get('/readyz')
    async def readyz() -> Response:
        # TODO: add real dependency checks (DB, cache, queue, etc.)
        return Response(
            content='{"status":"ready"}',
            media_type='application/json',
            status_code=200,
        )

    metrics_app = make_asgi_app()
    app.mount('/metrics', metrics_app)

    return app

from __future__ import annotations

from fastapi.testclient import TestClient

from app.config import AppConfig
from app.http import create_app


def test_healthz() -> None:
    config = AppConfig()
    app = create_app(config)
    client = TestClient(app)

    response = client.get('/healthz')

    assert response.status_code == 200
    assert response.json() == {'status': 'ok'}

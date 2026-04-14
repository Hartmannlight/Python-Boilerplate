from __future__ import annotations

import json
from urllib.error import URLError

import pytest

from python_boilerplate.config import Settings
from python_boilerplate.runtime.health import (
    HealthReport,
    check_health,
    emit_health_report,
    parse_prometheus_text,
)


def test_parse_prometheus_text_ignores_comments_and_labels() -> None:
    payload = "\n".join(
        [
            "# HELP app_up test",
            'app_info{version="0.1.0",commit="dev",env="test"} 1.0',
            "app_up 1.0",
            "last_success_timestamp_seconds 42.0",
        ]
    )

    assert parse_prometheus_text(payload) == {
        "app_up": 1.0,
        "last_success_timestamp_seconds": 42.0,
    }


def test_emit_health_report_prints_json(capsys: pytest.CaptureFixture[str]) -> None:
    report = HealthReport(
        service="demo",
        env="test",
        version="0.1.0",
        commit="dev",
        timestamp="1.23",
        ok=True,
        reason="ok",
    )

    exit_code = emit_health_report(report)
    captured = capsys.readouterr()

    assert exit_code == 0
    assert json.loads(captured.out) == {
        "service": "demo",
        "env": "test",
        "version": "0.1.0",
        "commit": "dev",
        "timestamp": "1.23",
        "ok": True,
        "reason": "ok",
    }


def test_check_health_returns_unhealthy_when_metrics_are_disabled() -> None:
    report = check_health(Settings(metrics_enabled=False))

    assert report.ok is True
    assert report.reason == "metrics_disabled"


def test_check_health_uses_configured_metrics_host(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    class ResponseStub:
        def __enter__(self) -> ResponseStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"app_up 1.0\nlast_progress_timestamp_seconds 9999999999.0\n"

    def urlopen_stub(url: str, timeout: int) -> ResponseStub:
        requested_urls.append(url)
        assert timeout == 2
        return ResponseStub()

    monkeypatch.setattr("python_boilerplate.runtime.health.urlopen", urlopen_stub)

    report = check_health(Settings(metrics_host="127.0.0.2", metrics_port=9100))

    assert report.ok is True
    assert requested_urls == ["http://127.0.0.2:9100/metrics"]


def test_check_health_maps_wildcard_host_to_loopback(monkeypatch: pytest.MonkeyPatch) -> None:
    requested_urls: list[str] = []

    def urlopen_stub(url: str, timeout: int) -> object:
        requested_urls.append(url)
        raise URLError("boom")

    monkeypatch.setattr("python_boilerplate.runtime.health.urlopen", urlopen_stub)

    report = check_health(Settings(metrics_host="0.0.0.0", metrics_port=9100))

    assert report.ok is False
    assert report.reason == "metrics_unreachable"
    assert requested_urls == ["http://127.0.0.1:9100/metrics"]


def test_check_health_accepts_missing_progress_metric(monkeypatch: pytest.MonkeyPatch) -> None:
    class ResponseStub:
        def __enter__(self) -> ResponseStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"app_up 1.0\n"

    monkeypatch.setattr(
        "python_boilerplate.runtime.health.urlopen",
        lambda _url, timeout: ResponseStub(),
    )

    report = check_health(Settings())

    assert report.ok is True
    assert report.reason == "ok"


def test_check_health_returns_structured_failure_for_invalid_metrics_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ResponseStub:
        def __enter__(self) -> ResponseStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return b"app_up definitely-not-a-number\n"

    monkeypatch.setattr(
        "python_boilerplate.runtime.health.urlopen",
        lambda _url, timeout: ResponseStub(),
    )

    report = check_health(Settings())

    assert report.ok is False
    assert report.reason == "metrics_invalid"


def test_check_health_prefers_last_success_for_freshness(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class ResponseStub:
        def __enter__(self) -> ResponseStub:
            return self

        def __exit__(self, *_args: object) -> None:
            return None

        def read(self) -> bytes:
            return (
                b"app_up 1.0\n"
                b"last_progress_timestamp_seconds 9999999999.0\n"
                b"last_success_timestamp_seconds 1.0\n"
            )

    monkeypatch.setattr(
        "python_boilerplate.runtime.health.urlopen",
        lambda _url, timeout: ResponseStub(),
    )
    monkeypatch.setattr("python_boilerplate.runtime.health.time", lambda: 100.0)

    report = check_health(Settings(health_max_age_seconds=10.0))

    assert report.ok is False
    assert report.reason == "stale"

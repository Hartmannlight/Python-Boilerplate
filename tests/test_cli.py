from __future__ import annotations

from argparse import Namespace

import pytest

from python_boilerplate import cli
from python_boilerplate.runtime.health import HealthReport


def test_main_dispatches_health(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "load_settings", lambda: object())
    monkeypatch.setattr(cli, "build_parser", lambda: _parser_stub(Namespace(command="health")))
    monkeypatch.setattr(
        cli,
        "check_health",
        lambda _settings: HealthReport(
            service="demo",
            env="test",
            version="0.1.0",
            commit="dev",
            timestamp="1.0",
            ok=True,
            reason="ok",
        ),
    )
    monkeypatch.setattr(cli, "emit_health_report", lambda report: 0 if report.ok else 1)

    assert cli.main() == 0


def test_main_dispatches_run(monkeypatch: pytest.MonkeyPatch) -> None:
    class ServiceStub:
        def run(self) -> int:
            return 0

    monkeypatch.setattr(cli, "load_settings", lambda: object())
    monkeypatch.setattr(cli, "build_parser", lambda: _parser_stub(Namespace(command="run")))
    monkeypatch.setattr(cli, "create_worker_service", lambda: ServiceStub())

    assert cli.main() == 0


def _parser_stub(namespace: Namespace) -> object:
    class ParserStub:
        def parse_args(self) -> Namespace:
            return namespace

    return ParserStub()

from __future__ import annotations

import pytest

from python_boilerplate.config import load_settings, parse_bool


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("true", True),
        ("TRUE", True),
        ("1", True),
        ("false", False),
        ("0", False),
        ("off", False),
    ],
)
def test_parse_bool_accepts_supported_values(value: str, expected: bool) -> None:
    assert parse_bool(value) is expected


def test_parse_bool_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        parse_bool("maybe")


def test_load_settings_reads_runtime_values_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_NAME", "demo")
    monkeypatch.setenv("APP_ENV", "test")
    monkeypatch.setenv("APP_DEBUG", "yes")
    monkeypatch.setenv("APP_METRICS_PORT", "9100")
    monkeypatch.setenv("APP_TRACES_ENABLED", "false")

    settings = load_settings()

    assert settings.service_name == "demo"
    assert settings.environment == "test"
    assert settings.debug is True
    assert settings.metrics_port == 9100
    assert settings.traces_enabled is False

import logging

import pytest

from konta.utils.logger import get_logger

_ENV_VAR = "LOG_LEVEL"


def test_get_logger_returns_configured_logger() -> None:
    logger = get_logger("konta.test_get_logger_returns_configured_logger")

    assert logger.level == logging.INFO
    assert len(logger.handlers) == 1
    assert isinstance(logger.handlers[0], logging.StreamHandler)
    assert logger.propagate is False


def test_get_logger_is_idempotent_per_name() -> None:
    first = get_logger("konta.test_get_logger_is_idempotent_per_name")
    second = get_logger("konta.test_get_logger_is_idempotent_per_name")

    assert first is second
    assert len(first.handlers) == 1


def test_get_logger_colors_messages_by_level(capsys: pytest.CaptureFixture[str]) -> None:
    logger = get_logger("konta.test_get_logger_colors_messages_by_level")

    logger.warning("careful")

    err = capsys.readouterr().err
    assert "\033[33m" in err
    assert "careful" in err
    assert "\033[0m" in err


def test_get_logger_reads_level_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_ENV_VAR, "debug")

    logger = get_logger("konta.test_get_logger_reads_level_from_env")

    assert logger.level == logging.DEBUG


def test_get_logger_explicit_level_overrides_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_ENV_VAR, "DEBUG")

    logger = get_logger("konta.test_get_logger_explicit_level_overrides_env", level=logging.ERROR)

    assert logger.level == logging.ERROR


def test_get_logger_raises_on_invalid_env_level(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(_ENV_VAR, "not-a-level")

    with pytest.raises(ValueError, match="Invalid LOG_LEVEL"):
        get_logger("konta.test_get_logger_raises_on_invalid_env_level")

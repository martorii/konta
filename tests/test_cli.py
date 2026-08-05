import subprocess
import sys

import pytest

from konta.cli import main


def test_main_runs(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert "Hello from konta!" in captured.out


def test_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "konta.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "konta" in result.stdout

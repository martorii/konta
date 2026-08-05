import subprocess
import sys
from pathlib import Path

import pytest

from konta.cli import main

DUMMY_HEADER = "Fecha,Concepto,Importe,Divisa\n"


def test_main_runs(capsys: pytest.CaptureFixture[str]) -> None:
    main([])
    captured = capsys.readouterr()
    assert "Hello from konta!" in captured.out


def test_run_prints_first_five_rows(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "a.csv").write_text(DUMMY_HEADER + "31/12/2025,AMAZON EU SARL,-45.99,EUR\n")

    main(["run", "--input", str(tmp_path), "--format", "dummy"])

    captured = capsys.readouterr()
    assert "AMAZON EU SARL" in captured.out


def test_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "konta.cli", "--version"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "konta" in result.stdout

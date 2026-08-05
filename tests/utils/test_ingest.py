from pathlib import Path

import pytest

from konta.utils.ingest import ingest_folder


def test_ingest_folder_concatenates_matching_csv_files(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x,y\n1,2\n")
    (tmp_path / "b.csv").write_text("x,y\n3,4\n")

    result = ingest_folder(tmp_path)

    assert list(result.columns) == ["x", "y"]
    assert result.to_dict("records") == [
        {"x": 1, "y": 2},
        {"x": 3, "y": 4},
    ]


def test_ingest_folder_ignores_non_csv_files(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x,y\n1,2\n")
    (tmp_path / "notes.txt").write_text("irrelevant")

    result = ingest_folder(tmp_path)

    assert list(result.columns) == ["x", "y"]
    assert len(result) == 1


def test_ingest_folder_raises_on_column_mismatch(tmp_path: Path) -> None:
    (tmp_path / "a.csv").write_text("x,y\n1,2\n")
    (tmp_path / "b.csv").write_text("x,z\n3,4\n")

    with pytest.raises(ValueError, match="Column mismatch"):
        ingest_folder(tmp_path)

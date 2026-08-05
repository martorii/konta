from pathlib import Path

import pandas as pd

from konta.utils.logger import get_logger

logger = get_logger(__name__)


def _read_file(path: Path) -> pd.DataFrame:
    """Read a single CSV file into a pandas DataFrame."""
    return pd.read_csv(path)



def _file_is_valid(path: Path) -> bool:
    """Return True if the path is a CSV file and is a pathlib Path."""
    if not isinstance(path, Path):
        return False
    suffix = path.suffix
    return suffix.lower() == ".csv"


def _check_matching_columns(paths: list[Path], frames: list[pd.DataFrame]) -> None:
    """Verify all DataFrames have matching columns, raise ValueError if not."""
    columns = frames[0].columns
    for path, frame in zip(paths, frames, strict=True):
        if not frame.columns.equals(columns):
            raise ValueError(
                f"Column mismatch in {path.name}: expected {list(columns)}, "
                f"got {list(frame.columns)}"
            )


def ingest_folder(folder: Path) -> pd.DataFrame:
    """Reads input folder and concatenates valid files into a pandas dataframe"""

    logger.info("Ingesting folder %s", folder)

    all_files = [path for path in sorted(folder.iterdir()) if path.is_file()]
    paths = [path for path in all_files if _file_is_valid(path)]
    logger.debug("Found %d files, %d valid CSV files", len(all_files), len(paths))

    skipped = [path for path in all_files if path not in paths]
    for path in skipped:
        logger.warning("Omitting invalid file %s", path.name)

    frames = [_read_file(path) for path in paths]

    try:
        _check_matching_columns(paths, frames)
    except ValueError:
        logger.error("Column mismatch across files in %s", folder)
        raise

    result = pd.concat(frames, ignore_index=True)
    logger.info("Ingested %d rows from %d files", len(result), len(paths))

    return result

from pathlib import Path
from typing import cast

import pandas as pd
from pydantic import ValidationError

from konta.models.formats import FORMAT_REGISTRY
from konta.models.formats.base import RawTransaction
from konta.models.Transaction import Transaction
from konta.utils.categorize import DEFAULT_RULES_PATH, categorize_transaction, load_rules
from konta.utils.logger import get_logger

logger = get_logger(__name__)


def _read_file(path: Path, raw_model: type[RawTransaction]) -> pd.DataFrame:
    """Read a single CSV file into a pandas DataFrame, using the format's read_csv kwargs."""
    return cast(pd.DataFrame, pd.read_csv(path, **raw_model.read_csv_kwargs))


def _file_is_valid(path: Path) -> bool:
    """Return True if the path is a CSV file and is a pathlib Path."""
    if not isinstance(path, Path):
        return False
    suffix = path.suffix
    return suffix.lower() == ".csv"


def _map_frame(
    path: Path, frame: pd.DataFrame, raw_model: type[RawTransaction]
) -> list[Transaction]:
    """Validate each row against the raw format model and convert it to canonical."""
    transactions = []
    for row in frame.to_dict("records"):
        str_keyed_row = {str(key): value for key, value in row.items()}
        try:
            raw = raw_model(**str_keyed_row)
        except ValidationError as e:
            raise ValueError(f"Invalid row in {path.name}: {e}") from e
        transactions.append(raw.to_canonical())
    return transactions


def ingest_transactions(
    folder: Path, format: str, rules_path: Path = DEFAULT_RULES_PATH
) -> list[Transaction]:
    """Reads input folder and maps valid files of the given format into categorized transactions."""

    logger.info("Ingesting folder %s with format %s", folder, format)

    raw_model = FORMAT_REGISTRY.get(format)
    if raw_model is None:
        raise ValueError(f"Unknown format: {format!r}. Available: {sorted(FORMAT_REGISTRY)}")

    all_files = [path for path in sorted(folder.iterdir()) if path.is_file()]
    paths = [path for path in all_files if _file_is_valid(path)]
    logger.debug("Found %d files, %d valid CSV files", len(all_files), len(paths))

    skipped = [path for path in all_files if path not in paths]
    for path in skipped:
        logger.warning("Omitting invalid file %s", path.name)

    if not paths:
        logger.info("No valid CSV files found in %s, nothing to ingest", folder)
        return []

    transactions: list[Transaction] = []
    for path in paths:
        frame = _read_file(path, raw_model)
        try:
            transactions.extend(_map_frame(path, frame, raw_model))
        except ValueError:
            logger.error("Failed to map rows in %s to format %s", path.name, format)
            raise

    rules = load_rules(rules_path)
    try:
        transactions = [categorize_transaction(t, rules) for t in transactions]
    except ValueError:
        logger.error("Failed to categorize transactions ingested from %s", folder)
        raise

    logger.info("Ingested %d rows from %d files", len(transactions), len(paths))

    return transactions


def ingest_folder(
    folder: Path, format: str, rules_path: Path = DEFAULT_RULES_PATH
) -> pd.DataFrame:
    """Reads input folder and returns categorized transactions of the given format as a frame."""
    transactions = ingest_transactions(folder, format, rules_path)
    return pd.DataFrame([t.model_dump() for t in transactions])

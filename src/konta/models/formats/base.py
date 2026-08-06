from abc import ABC, abstractmethod
from typing import Any, ClassVar

from pydantic import BaseModel

from konta.models.Transaction import Transaction


class RawTransaction(BaseModel, ABC):
    """Base for per-format raw row models; each format converts itself to canonical."""

    # Extra kwargs passed to pandas.read_csv when reading this format's files.
    read_csv_kwargs: ClassVar[dict[str, Any]] = {}

    @abstractmethod
    def to_canonical(self) -> Transaction: ...

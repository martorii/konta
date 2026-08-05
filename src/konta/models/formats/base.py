from abc import ABC, abstractmethod

from pydantic import BaseModel

from konta.models.Transaction import Transaction


class RawTransaction(BaseModel, ABC):
    """Base for per-format raw row models; each format converts itself to canonical."""

    @abstractmethod
    def to_canonical(self) -> Transaction: ...

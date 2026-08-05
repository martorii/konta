from konta.models.formats.base import RawTransaction
from konta.models.formats.Dummy import DummyTransaction

FORMAT_REGISTRY: dict[str, type[RawTransaction]] = {
    "dummy": DummyTransaction,
}

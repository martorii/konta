import re
from pathlib import Path

import yaml

from konta.models.Transaction import Transaction

DEFAULT_RULES_PATH = Path(__file__).resolve().parent.parent / "config" / "categories.yaml"

CategoryRules = dict[str, list[re.Pattern[str]]]


def load_rules(path: Path = DEFAULT_RULES_PATH) -> CategoryRules:
    """Load category -> compiled regex pattern rules from a YAML file."""
    raw: dict[str, list[str]] = yaml.safe_load(path.read_text()) or {}
    return {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in raw.items()
    }


def save_rules(rules: CategoryRules, path: Path = DEFAULT_RULES_PATH) -> None:
    """Persist category -> pattern rules back to a YAML file."""
    raw = {
        category: [pattern.pattern for pattern in patterns] for category, patterns in rules.items()
    }
    path.write_text(yaml.safe_dump(raw, allow_unicode=True, sort_keys=True))


def categorize(counterparty: str, rules: CategoryRules) -> str | None:
    """Match a counterparty string against category rules.

    Returns the matching category, or None if no rule matches. Raises ValueError
    if more than one category matches, since categories must be mutually exclusive.
    """
    matches = sorted(
        category
        for category, patterns in rules.items()
        if any(pattern.search(counterparty) for pattern in patterns)
    )

    if len(matches) > 1:
        raise ValueError(f"Counterparty {counterparty!r} matches multiple categories: {matches}")

    return matches[0] if matches else None


def categorize_transaction(transaction: Transaction, rules: CategoryRules) -> Transaction:
    """Return a copy of `transaction` with `category` set from the given rules."""
    category = categorize(transaction.counterparty, rules)
    return transaction.model_copy(update={"category": category})

import datetime
import re
from decimal import Decimal
from pathlib import Path

import pytest

from konta.models.Transaction import Transaction
from konta.utils.categorize import (
    CategoryRules,
    categorize,
    categorize_transaction,
    load_rules,
    save_rules,
)


def _rules(**category_to_patterns: list[str]) -> CategoryRules:
    return {
        category: [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
        for category, patterns in category_to_patterns.items()
    }


def test_categorize_returns_matching_category() -> None:
    rules = _rules(groceries=["REWE"])

    assert categorize("REWE SAGT DANKE", rules) == "groceries"


def test_categorize_is_case_insensitive() -> None:
    rules = _rules(groceries=["rewe"])

    assert categorize("REWE SAGT DANKE", rules) == "groceries"


def test_categorize_returns_none_when_no_pattern_matches() -> None:
    rules = _rules(groceries=["REWE"])

    assert categorize("AMAZON EU SARL", rules) is None


def test_categorize_raises_when_multiple_categories_match() -> None:
    rules = _rules(shopping=["AMAZON"], retail=["EU SARL"])

    with pytest.raises(ValueError, match="multiple categories"):
        categorize("AMAZON EU SARL", rules)


def test_categorize_transaction_sets_category() -> None:
    rules = _rules(groceries=["REWE"])
    txn = Transaction(
        date=datetime.date(2025, 12, 31),
        amount=Decimal("-10"),
        currency="EUR",
        counterparty="REWE SAGT DANKE",
    )

    categorized = categorize_transaction(txn, rules)

    assert categorized.category == "groceries"
    assert txn.category is None


def test_load_rules_compiles_patterns(tmp_path: Path) -> None:
    path = tmp_path / "categories.yaml"
    path.write_text("groceries:\n  - REWE\n  - ALDI\n")

    rules = load_rules(path)

    assert set(rules) == {"groceries"}
    assert [p.pattern for p in rules["groceries"]] == ["REWE", "ALDI"]


def test_load_rules_returns_empty_dict_for_empty_file(tmp_path: Path) -> None:
    path = tmp_path / "categories.yaml"
    path.write_text("{}\n")

    assert load_rules(path) == {}


def test_save_rules_round_trips(tmp_path: Path) -> None:
    path = tmp_path / "categories.yaml"
    rules = _rules(groceries=["REWE", "ALDI"])

    save_rules(rules, path)
    loaded = load_rules(path)

    assert [p.pattern for p in loaded["groceries"]] == ["REWE", "ALDI"]

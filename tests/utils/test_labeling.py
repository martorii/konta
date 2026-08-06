import datetime
import re
from decimal import Decimal
from pathlib import Path

import pytest

from konta.models.Transaction import Transaction
from konta.utils.categorize import CategoryRules, load_rules
from konta.utils.labeling import add_rule, find_uncategorized, label_interactively


def _txn(counterparty: str) -> Transaction:
    return Transaction(
        date=datetime.date(2025, 12, 31),
        amount=Decimal("-10"),
        currency="EUR",
        counterparty=counterparty,
    )


def test_find_uncategorized_returns_distinct_unmatched_counterparties() -> None:
    transactions = [_txn("REWE SAGT DANKE"), _txn("AMAZON EU SARL"), _txn("AMAZON EU SARL")]

    assert find_uncategorized(transactions, rules={}) == ["REWE SAGT DANKE", "AMAZON EU SARL"]


def test_find_uncategorized_excludes_already_matched_counterparties() -> None:
    rules: CategoryRules = {"groceries": [re.compile("REWE")]}
    transactions = [_txn("REWE SAGT DANKE"), _txn("AMAZON EU SARL")]

    assert find_uncategorized(transactions, rules) == ["AMAZON EU SARL"]


def test_add_rule_adds_escaped_literal_pattern() -> None:
    rules: CategoryRules = {}

    add_rule("groceries", "REWE SAGT DANKE", rules)

    assert rules["groceries"][0].search("REWE SAGT DANKE")
    assert rules["groceries"][0].search("OTHER") is None


def test_add_rule_raises_on_conflict_with_existing_category() -> None:
    rules: CategoryRules = {"groceries": [re.compile("REWE")]}

    with pytest.raises(ValueError, match="already matches"):
        add_rule("retail", "REWE SAGT DANKE", rules)


def test_label_interactively_writes_new_rule(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = tmp_path / "categories.yaml"
    rules_path.write_text("{}\n")
    transactions = [_txn("REWE SAGT DANKE")]

    monkeypatch.setattr("builtins.input", lambda _: "groceries")

    label_interactively(transactions, rules_path)

    rules = load_rules(rules_path)
    assert "groceries" in rules
    assert rules["groceries"][0].search("REWE SAGT DANKE")


def test_label_interactively_skips_blank_input(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = tmp_path / "categories.yaml"
    rules_path.write_text("{}\n")
    transactions = [_txn("REWE SAGT DANKE")]

    monkeypatch.setattr("builtins.input", lambda _: "")

    label_interactively(transactions, rules_path)

    assert load_rules(rules_path) == {}


def test_label_interactively_does_nothing_when_all_categorized(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rules_path = tmp_path / "categories.yaml"
    rules_path.write_text("groceries:\n  - REWE\n")
    transactions = [_txn("REWE SAGT DANKE")]

    def _fail_input(_: str) -> str:
        raise AssertionError("input() should not be called when nothing is uncategorized")

    monkeypatch.setattr("builtins.input", _fail_input)

    label_interactively(transactions, rules_path)

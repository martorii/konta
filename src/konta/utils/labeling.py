import re
import string
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.categorize import CategoryRules, categorize, load_rules, save_rules
from konta.utils.logger import get_logger

logger = get_logger(__name__)


def find_uncategorized(transactions: list[Transaction], rules: CategoryRules) -> list[str]:
    """Return distinct counterparty strings that match no existing rule."""
    return list(
        dict.fromkeys(
            t.counterparty for t in transactions if categorize(t.counterparty, rules) is None
        )
    )


def add_rule(category: str, counterparty: str, rules: CategoryRules) -> None:
    """Add a literal, escaped pattern for `counterparty` under `category`, in place.

    Regex-generalization of this pattern (e.g. via an LLM) is a follow-up task;
    for now the pattern is the exact counterparty string, case-insensitively matched.

    Raises ValueError if `counterparty` already matches an existing category, since
    categorization must stay unambiguous (a counterparty may match at most one rule).
    """
    existing = categorize(counterparty, rules)
    if existing is not None:
        raise ValueError(f"{counterparty!r} already matches existing category {existing!r}")

    pattern = re.compile(re.escape(counterparty), re.IGNORECASE)
    rules.setdefault(category, []).append(pattern)


def _print_category_menu(categories: list[str]) -> dict[str, str]:
    """Print a lettered menu of existing categories; return a letter -> category map."""
    letter_map = dict(zip(string.ascii_uppercase, categories, strict=False))
    if letter_map:
        print("Existing categories:")
        for letter, category in letter_map.items():
            print(f"  {letter}) {category}")
    else:
        print("No categories yet.")
    return letter_map


def _prompt_category(counterparty: str, letter_map: dict[str, str]) -> str:
    """Ask the user for a category: a menu letter, a new category name, or blank to skip."""
    raw = input(f"Category for {counterparty!r} (letter, new name, or blank to skip): ").strip()
    return letter_map.get(raw.upper(), raw)


def label_interactively(transactions: list[Transaction], rules_path: Path) -> None:
    """Prompt the user, one at a time, to assign a category to each uncategorized counterparty.

    Existing categories are shown as a lettered menu so they can be picked without
    retyping the name; typing a name not on the menu creates a new category. Rules
    are written back to `rules_path` once labelling is done.
    """
    rules = load_rules(rules_path)
    uncategorized = find_uncategorized(transactions, rules)

    if not uncategorized:
        logger.info("No uncategorized counterparties found")
        return

    for counterparty in uncategorized:
        letter_map = _print_category_menu(sorted(rules))
        category = _prompt_category(counterparty, letter_map)
        if not category:
            continue
        try:
            add_rule(category, counterparty, rules)
        except ValueError as e:
            logger.warning("Skipping %r: %s", counterparty, e)

    save_rules(rules, rules_path)

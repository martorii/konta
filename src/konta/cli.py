import argparse
from importlib.metadata import version
from pathlib import Path

from konta.models.formats import FORMAT_REGISTRY
from konta.utils.categorize import DEFAULT_RULES_PATH
from konta.utils.ingest import ingest_folder, ingest_transactions
from konta.utils.labeling import label_interactively


def _add_input_args(subparser: argparse.ArgumentParser) -> None:
    subparser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the input folder containing files to ingest",
    )
    subparser.add_argument(
        "--format",
        choices=sorted(FORMAT_REGISTRY),
        default="dummy",
        help="Input file format (default: %(default)s)",
    )
    subparser.add_argument(
        "--rules",
        type=Path,
        default=DEFAULT_RULES_PATH,
        help="Path to the category rules YAML file (default: %(default)s)",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="konta", description="konta CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('konta')}",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Ingest an input folder")
    _add_input_args(run_parser)

    label_parser = subparsers.add_parser(
        "label", help="Interactively assign categories to uncategorized transactions"
    )
    _add_input_args(label_parser)
    label_parser.add_argument(
        "-n",
        "--limit",
        type=int,
        default=None,
        help="Only label the first N unlabelled entries",
    )

    return parser


def _run(input_folder: Path, format: str, rules_path: Path) -> None:
    result = ingest_folder(input_folder, format=format, rules_path=rules_path)
    print(result.head())


def _label(input_folder: Path, format: str, rules_path: Path, limit: int | None) -> None:
    transactions = ingest_transactions(input_folder, format=format, rules_path=rules_path)
    label_interactively(transactions, rules_path, limit=limit)


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    match args.command:
        case "run":
            _run(args.input, args.format, args.rules)
        case "label":
            _label(args.input, args.format, args.rules, args.limit)
        case _:
            print("Hello from konta!")


if __name__ == "__main__":
    main()

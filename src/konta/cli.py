import argparse
from importlib.metadata import version
from pathlib import Path

from konta.models.formats import FORMAT_REGISTRY
from konta.utils.ingest import ingest_folder


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="konta", description="konta CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('konta')}",
    )

    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Ingest an input folder")
    run_parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to the input folder containing files to ingest",
    )
    run_parser.add_argument(
        "--format",
        choices=sorted(FORMAT_REGISTRY),
        default="dummy",
        help="Input file format (default: %(default)s)",
    )

    return parser


def _run(input_folder: Path, format: str) -> None:
    result = ingest_folder(input_folder, format=format)
    print(result.head())


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        _run(args.input, args.format)
    else:
        print("Hello from konta!")


if __name__ == "__main__":
    main()

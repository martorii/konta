import argparse
from importlib.metadata import version


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="konta", description="konta CLI")
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {version('konta')}",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    parser.parse_args(argv)
    print("Hello from konta!")


if __name__ == "__main__":
    main()

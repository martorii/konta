# konta

A CLI for ingesting bank transaction exports, categorizing them by counterparty, and
generating a self-contained HTML spend-by-category report.

## Installation

Requires Python 3.13+ and [uv](https://docs.astral.sh/uv/).

```sh
uv sync
```

Copy `.env.example` to `.env` if you want to override the default log level:

```sh
cp .env.example .env
```

## Usage

Run commands with `uv run konta <command>`.

### `run`

Ingest a folder of transaction files and print a preview.

```sh
uv run konta run --input input/ --format dkb
```

### `label`

Interactively assign categories to counterparties that don't yet match a rule. For
each uncategorized counterparty, pick an existing category from the menu, type a new
category name, or leave blank to skip. Rules are saved back to the rules file when done.

```sh
uv run konta label --input input/ --format dkb -n 20
```

### `report`

Generate an HTML report summarizing spend by category.

```sh
uv run konta report --input input/ --format dkb --output output/report.html
```

### Shared options

- `--input` (required): folder containing the files to ingest.
- `--format`: input file format, one of `dummy`, `dkb` (default: `dummy`).
- `--rules`: path to the category rules YAML file (default: `src/konta/config/categories.yaml`).

## Supported formats

| Format  | Description                                  |
|---------|-----------------------------------------------|
| `dummy` | Spanish-bank-like CSV (`Fecha`, `Concepto`, `Importe`, `Divisa`) |
| `dkb`   | DKB (Deutsche Kreditbank) Girokonto CSV export |

New formats are added by implementing `RawTransaction` in
`src/konta/models/formats/` and registering it in `FORMAT_REGISTRY`.

## Categorization rules

Rules map a category name to a list of regex patterns matched against the transaction
counterparty (case-insensitively). They live in a YAML file, by default
`src/konta/config/categories.yaml`, which is gitignored since it's user-specific.

```yaml
Groceries:
  - "SUPERMARKET"
  - "GROCER"
```

A counterparty must match at most one category's patterns; ambiguous matches raise an
error, so keep patterns mutually exclusive.

## Development

```sh
uv run ruff check .
uv run mypy
uv run pytest
```

See `CLAUDE.md` for full project conventions.

# 💰 konta

**A CLI that turns messy bank exports into a clean, categorized spending report.**

Ingest transaction files from your bank, auto-categorize them by counterparty, and
generate a self-contained HTML report — all from the terminal.

![Python](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)
![uv](https://img.shields.io/badge/managed%20with-uv-DE5FE9?logo=uv&logoColor=white)
![mypy](https://img.shields.io/badge/mypy-strict-2A6DB2)
![ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)
![status](https://img.shields.io/badge/status-v0.1.0-orange)

---

## ✨ Features

- 📥 **Ingest** transaction exports from multiple bank formats
- 🏷️ **Auto-categorize** transactions via regex rules matched against counterparties
- 🖊️ **Interactive labeling** for anything that doesn't yet match a rule
- 📊 **Self-contained HTML reports** — spend broken down by category, no server needed
- 🔒 **Local-first** — your data and rules never leave your machine
- 🧩 **Pluggable formats** — add a new bank in one file

## 🚀 Installation

Requires **Python 3.13+** and [**uv**](https://docs.astral.sh/uv/).

```sh
uv sync
```

Optionally override the default log level:

```sh
cp .env.example .env
```

## 🛠️ Usage

Run everything through `uv run konta <command>`.

### `run` — preview your transactions

```sh
uv run konta run --input input/ --format dkb
```

Ingests a folder of transaction files and prints a preview.

### `label` — teach konta your categories

```sh
uv run konta label --input input/ --format dkb -n 20
```

Interactively assign categories to counterparties that don't yet match a rule. For
each uncategorized counterparty, pick an existing category from the menu, type a new
category name, or leave blank to skip. Rules are saved back to the rules file when done.

### `report` — generate the HTML report

```sh
uv run konta report --input input/ --format dkb --output output/report.html
```

Produces a self-contained HTML report summarizing spend by category — open it in any
browser, no dependencies required.

### ⚙️ Shared options

| Option     | Description                                                          |
|------------|-----------------------------------------------------------------------|
| `--input`  | **(required)** folder containing the files to ingest                  |
| `--format` | input file format, one of `dummy`, `dkb` (default: `dummy`)          |
| `--rules`  | path to the category rules YAML file (default: `src/konta/config/categories.yaml`) |

## 🏦 Supported formats

| Format  | Description                                  |
|---------|-----------------------------------------------|
| `dummy` | Spanish-bank-like CSV (`Fecha`, `Concepto`, `Importe`, `Divisa`) |
| `dkb`   | DKB (Deutsche Kreditbank) Girokonto CSV export |

New formats are added by implementing `RawTransaction` in
`src/konta/models/formats/` and registering it in `FORMAT_REGISTRY`.

## 🏷️ Categorization rules

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

## 🧪 Development

```sh
uv run ruff check .
uv run mypy
uv run pytest
```

See [`CLAUDE.md`](./CLAUDE.md) for full project conventions.

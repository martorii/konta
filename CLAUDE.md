# CLAUDE.md

Guidance for working on the `konta` CLI project.

## Project setup

- Package management: `uv` (see `uv.lock`). Use `uv sync` to install, `uv run <cmd>` to run tools/scripts.
- Python: 3.13+ only. Use modern syntax (`X | None`, `list[str]`, `match` statements) — no `typing.Optional`/`typing.List`/`typing.Union`.
- Source lives under `src/konta`, tests under `tests`.

## Before finishing any change

Run these three checks; all must pass:

```
uv run ruff check .
uv run mypy
uv run pytest
```

## Linting (ruff)

Enabled rule sets: `E`, `F`, `I`, `UP`, `B`, `SIM` (pycodestyle errors, pyflakes, isort, pyupgrade, bugbear, simplify). Line length is 100.

- Keep imports sorted (`I`) — let ruff's `--fix` handle it rather than hand-ordering.
- Prefer the modern/idiomatic form ruff's `UP` and `SIM` rules push toward (e.g. f-strings over `.format`, comprehensions over manual loops, ternaries where they're clearer) — don't fight the linter.
- Watch for the mutable-default and other `B` (bugbear) footguns, e.g. no mutable default arguments.

## Typing (mypy strict)

`mypy` runs in `strict` mode against `src` and `tests`. This means:

- Every function needs full type annotations (params and return type), including `-> None`.
- No implicit `Any` — untyped third-party imports need a `# type: ignore` with a reason, or a stub.
- No unchecked use of `Optional`/`None` without narrowing.

Write code that satisfies strict mode from the start rather than adding annotations after the fact.

## Tests

- Tests live in `tests/`, mirroring the `src/konta` layout, and run via `pytest` (configured in `pyproject.toml`).
- Add/update tests alongside behavior changes; don't rely on manual verification alone.

## Logging

- Use `konta.utils.logger.get_logger(__name__)` to get a module-level logger — don't call `logging.getLogger` directly or configure handlers by hand.
- It's console-only (stderr), colors output by level (DEBUG cyan, INFO green, WARNING yellow, ERROR red, CRITICAL bold red), and is safe to call repeatedly per name (no duplicate handlers).
- Use `logger.debug` for internal/diagnostic detail, `logger.info` for normal progress/status, `logger.warning` for recoverable issues, `logger.error`/`logger.critical` for failures. Don't use `print` for anything but final user-facing CLI output.
- Level defaults to `LOG_LEVEL` in `.env` (falls back to `INFO` if unset), loaded automatically via `python-dotenv`. Copy `.env.example` to `.env` to override locally; `.env` itself is gitignored, only `.env.example` is committed.

## General style

- Use inline comments when you need them.
- Favor small, focused functions over premature abstraction — this is an early-stage CLI project (`v0.1.0`), so avoid over-engineering for hypothetical future requirements.
- Use light-weighted docstrings. Consider using full docstrings only if the function is very complex or has many parameters.
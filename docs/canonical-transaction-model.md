# Canonical transaction model — design

Design agreed for mapping per-issuer CSV rows to a shared canonical model in `src/konta/utils/ingest.py`.

## Canonical model

Pydantic `BaseModel` (new dependency — add `pydantic` to `pyproject.toml`).

| Field | Type | Notes |
|---|---|---|
| `id` | `str` | Hash over `(date, amount, currency, counterparty)`. Deterministic; no row-index tiebreaker, so two genuinely identical transactions on the same day will collide onto the same `id` — accepted tradeoff. |
| `date` | `date` | Transaction date. |
| `amount` | `Decimal` | Always signed: positive = credit, negative = debit. |
| `currency` | `str` | ISO 4217 code (e.g. `EUR`). |
| `counterparty` | `str` | Free text — who sent/received the money. Collapsed with description/memo into a single field; no need to split until a real format demands it. |

Explicitly excluded for now: `source` (which issuer/account a row came from) — only one source is handled at a time, add back if/when multiple sources are ingested together.

## Mapping architecture

- **Registry of per-format raw pydantic models**, not a registry of plain functions. Each format gets its own raw model declaring the source's actual columns/types, plus a `to_canonical()` method converting to the canonical model. This gives two validation passes: "does this row match the expected raw shape" and "does it convert cleanly to canonical."
- Registry keyed by an explicit **format name**, passed in by the caller (e.g. `ingest_folder(folder, format="dummy")`). No auto-detection by column signature — not worth the complexity with only one format to validate it against.
- **One format per `ingest_folder` call** — a folder is assumed to hold files from a single issuer/format. Mixed-format folders are out of scope until there's a real need.

## Dummy format (for initial implementation)

Modeled loosely on a Spanish bank export — deliberately not a 1:1 copy of the canonical shape, so the mapper does real work (renaming, date reformatting):

```csv
Fecha,Concepto,Importe,Divisa
31/12/2025,AMAZON EU SARL,-45.99,EUR
30/12/2025,NOMINA EMPRESA SL,1500.00,EUR
```

| Raw column | Format | Maps to |
|---|---|---|
| `Fecha` | `DD/MM/YYYY` | `date` |
| `Concepto` | free text | `counterparty` |
| `Importe` | signed decimal string | `amount` |
| `Divisa` | ISO 4217 code | `currency` |

## Open items for implementation

- Add `pydantic` to `pyproject.toml` dependencies.
- `_check_matching_columns` in the current `ingest.py` assumes raw-column equality across files in a folder; needs to be reconciled with (or replaced by) per-row raw-model validation once mapping is introduced.
- Decide where mapping happens in the pipeline: per-file after `_read_file`, before `pd.concat`, so the concatenated result is already canonical rows.

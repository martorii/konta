from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.logger import get_logger

logger = get_logger(__name__)

UNCATEGORIZED = "Uncategorized"


@dataclass
class CategorySummary:
    category: str
    total: Decimal
    count: int

    @property
    def average(self) -> Decimal:
        return self.total / self.count


def _summarize(outgoing: list[Transaction]) -> list[CategorySummary]:
    """Aggregate outgoing transactions into per-category totals, sorted by spend descending."""
    totals: dict[str, Decimal] = {}
    counts: dict[str, int] = {}
    for t in outgoing:
        category = t.category or UNCATEGORIZED
        totals[category] = totals.get(category, Decimal(0)) + (-t.amount)
        counts[category] = counts.get(category, 0) + 1

    summaries = [
        CategorySummary(category, totals[category], counts[category]) for category in totals
    ]
    return sorted(summaries, key=lambda s: s.total, reverse=True)


def _render_bar(
    summary: CategorySummary, max_total: Decimal, total_spend: Decimal, currency: str
) -> str:
    width = float(summary.total / max_total * 100)
    share = float(summary.total / total_spend * 100)
    return f"""
    <div class="bar-row">
      <div class="bar-label">{summary.category}</div>
      <div class="bar-track"><div class="bar-fill" style="width: {width:.2f}%"></div></div>
      <div class="bar-value">{summary.total:.2f} {currency} ({share:.1f}%)</div>
    </div>"""


def _render_table_row(summary: CategorySummary, total_spend: Decimal, currency: str) -> str:
    share = float(summary.total / total_spend * 100)
    return f"""
    <tr>
      <td>{summary.category}</td>
      <td>{summary.total:.2f} {currency} ({share:.1f}%)</td>
      <td>{summary.count}</td>
      <td>{summary.average:.2f} {currency}</td>
    </tr>"""


def render_report(transactions: list[Transaction]) -> str:
    """Render a self-contained HTML spend-by-category report from a list of transactions."""
    outgoing = [t for t in transactions if t.amount < 0]

    if not outgoing:
        body = "<p>No outgoing transactions found.</p>"
    else:
        currency = outgoing[0].currency
        summaries = _summarize(outgoing)
        total_spend = sum((s.total for s in summaries), Decimal(0))
        start = min(t.date for t in outgoing)
        end = max(t.date for t in outgoing)
        max_total = summaries[0].total

        bars = "".join(_render_bar(s, max_total, total_spend, currency) for s in summaries)
        rows = "".join(_render_table_row(s, total_spend, currency) for s in summaries)

        body = f"""
        <p class="summary">
          {start.isoformat()} &ndash; {end.isoformat()} &middot;
          {len(outgoing)} transactions &middot;
          total spend {total_spend:.2f} {currency}
        </p>
        <div class="chart">{bars}</div>
        <table>
          <thead><tr><th>Category</th><th>Total</th><th>Count</th><th>Average</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>"""

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>konta report</title>
<style>
  body {{ font-family: system-ui, sans-serif; margin: 2rem auto; max-width: 800px; color: #111; }}
  h1 {{ margin-bottom: 0.25rem; }}
  .summary {{ color: #555; margin-top: 0; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.75rem; margin: 0.4rem 0; }}
  .bar-label {{ width: 140px; flex-shrink: 0; text-align: right; font-size: 0.9rem; }}
  .bar-track {{ flex: 1; background: #eee; border-radius: 4px; overflow: hidden; }}
  .bar-fill {{ background: #4a7dfc; height: 1.1rem; }}
  .bar-value {{ width: 110px; flex-shrink: 0; font-size: 0.85rem; color: #333; }}
  table {{ border-collapse: collapse; margin-top: 2rem; width: 100%; }}
  th, td {{ text-align: left; padding: 0.4rem 0.75rem; border-bottom: 1px solid #ddd; }}
  th {{ color: #555; font-weight: 600; }}
</style>
</head>
<body>
<h1>konta report</h1>
{body}
</body>
</html>
"""


def generate_report(transactions: list[Transaction], output_path: Path) -> Path:
    """Render the report and write it to `output_path`, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(transactions))
    logger.info("Wrote report to %s", output_path)
    return output_path

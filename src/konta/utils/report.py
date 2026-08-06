from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.logger import get_logger

logger = get_logger(__name__)

UNCATEGORIZED = "Uncategorized"
AVERAGING_WINDOW_DAYS = 30


@dataclass
class CategoryAverage:
    category: str
    avg_30d: Decimal


def _summarize(outgoing: list[Transaction]) -> list[CategoryAverage]:
    """Aggregate outgoing transactions into per-category 30-day average spend, sorted descending."""
    start = min(t.date for t in outgoing)
    end = max(t.date for t in outgoing)
    range_days = max((end - start).days, 1)
    factor = Decimal(AVERAGING_WINDOW_DAYS) / range_days

    totals: dict[str, Decimal] = {}
    for t in outgoing:
        category = t.category or UNCATEGORIZED
        totals[category] = totals.get(category, Decimal(0)) + (-t.amount)

    averages = [CategoryAverage(category, total * factor) for category, total in totals.items()]
    return sorted(averages, key=lambda a: a.avg_30d, reverse=True)


def _render_bar(average: CategoryAverage, max_avg: Decimal, currency: str) -> str:
    width = float(average.avg_30d / max_avg * 100)
    return f"""
    <div class="bar-row">
      <div class="bar-label">{average.category}</div>
      <div class="bar-track">
        <div class="bar-fill" style="width: {width:.2f}%"></div>
      </div>
      <div class="bar-value">{average.avg_30d:.2f} {currency}</div>
    </div>"""


def render_report(transactions: list[Transaction]) -> str:
    """Render a self-contained HTML report of 30-day average spend per category."""
    outgoing = [t for t in transactions if t.amount < 0]

    if not outgoing:
        body = "<p>No outgoing transactions found.</p>"
    else:
        currency = outgoing[0].currency
        averages = _summarize(outgoing)
        max_avg = averages[0].avg_30d
        total_avg = sum((a.avg_30d for a in averages), Decimal(0))

        bars = "".join(_render_bar(a, max_avg, currency) for a in averages)
        body = f"""<div class="total">
      <div class="total-label">30-day average total spend</div>
      <div class="total-value">{total_avg:.2f} {currency}</div>
    </div>
    <div class="chart">{bars}</div>"""

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>konta report</title>
<style>
  .viz-root {{
    color-scheme: light;
    --surface-1:      #fcfcfb;
    --page-plane:      #f9f9f7;
    --text-primary:   #0b0b0b;
    --text-secondary: #52514e;
    --text-muted:     #898781;
    --gridline:       #e1e0d9;
    --series-1:       #2a78d6;
  }}
  @media (prefers-color-scheme: dark) {{
    :root:where(:not([data-theme="light"])) .viz-root {{
      color-scheme: dark;
      --surface-1:      #1a1a19;
      --page-plane:      #0d0d0d;
      --text-primary:   #ffffff;
      --text-secondary: #c3c2b7;
      --text-muted:     #898781;
      --gridline:       #2c2c2a;
      --series-1:       #3987e5;
    }}
  }}
  :root[data-theme="dark"] .viz-root {{
    color-scheme: dark;
    --surface-1:      #1a1a19;
    --page-plane:      #0d0d0d;
    --text-primary:   #ffffff;
    --text-secondary: #c3c2b7;
    --text-muted:     #898781;
    --gridline:       #2c2c2a;
    --series-1:       #3987e5;
  }}
  .viz-root {{
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
    background: var(--page-plane);
    color: var(--text-primary);
    margin: 0;
    padding: 2rem;
  }}
  .card {{
    max-width: 800px;
    margin: 0 auto;
    background: var(--surface-1);
    border-radius: 8px;
    padding: 1.5rem 2rem 2rem;
  }}
  h1 {{ margin: 0 0 0.25rem; font-size: 1.25rem; }}
  .subtitle {{ color: var(--text-secondary); margin: 0 0 1.5rem; font-size: 0.9rem; }}
  .total {{
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    padding: 0.75rem 1rem;
    margin: 0 0 1.5rem;
    background: var(--page-plane);
    border-radius: 6px;
  }}
  .total-label {{ font-size: 0.85rem; color: var(--text-secondary); }}
  .total-value {{
    font-size: 1.25rem;
    font-weight: 600;
    font-variant-numeric: tabular-nums;
  }}
  .chart {{ display: flex; flex-direction: column; gap: 0.6rem; }}
  .bar-row {{ display: flex; align-items: center; gap: 0.75rem; }}
  .bar-label {{
    width: 140px;
    flex-shrink: 0;
    text-align: right;
    font-size: 0.85rem;
    color: var(--text-secondary);
  }}
  .bar-track {{
    flex: 1;
    background: var(--gridline);
    border-radius: 4px;
    height: 20px;
  }}
  .bar-fill {{
    background: var(--series-1);
    height: 100%;
    border-radius: 0 4px 4px 0;
  }}
  .bar-value {{
    width: 110px;
    flex-shrink: 0;
    font-size: 0.85rem;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
  }}
</style>
</head>
<body>
<div class="viz-root">
  <div class="card">
    <h1>konta report</h1>
    <p class="subtitle">30-day average spend per category</p>
    {body}
  </div>
</div>
</body>
</html>
"""


def generate_report(transactions: list[Transaction], output_path: Path) -> Path:
    """Render the report and write it to `output_path`, creating parent directories as needed."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_report(transactions))
    logger.info("Wrote report to %s", output_path)
    return output_path

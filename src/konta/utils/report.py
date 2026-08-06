from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from konta.models.Transaction import Transaction
from konta.utils.logger import get_logger

logger = get_logger(__name__)

UNCATEGORIZED = "Uncategorized"
IGNORED_CATEGORIES = {"Ignore"}
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


def _render_transaction_row(t: Transaction) -> str:
    return f"""
      <tr>
        <td data-sort="{t.date.isoformat()}">{t.date.isoformat()}</td>
        <td>{t.counterparty}</td>
        <td>{t.category or UNCATEGORIZED}</td>
        <td data-sort="{t.amount}" class="num">{t.amount:.2f}</td>
        <td>{t.currency}</td>
      </tr>"""


def _render_category_options(transactions: list[Transaction]) -> str:
    categories = sorted({t.category or UNCATEGORIZED for t in transactions})
    options = "".join(f'<option value="{c}">{c}</option>' for c in categories)
    return f'<option value="">All categories</option>{options}'


def _render_transactions_table(transactions: list[Transaction]) -> str:
    rows = "".join(_render_transaction_row(t) for t in transactions)
    category_options = _render_category_options(transactions)
    return f"""
    <div class="table-wrap">
      <div class="table-controls">
        <label for="tx-category-filter">Category</label>
        <select id="tx-category-filter">{category_options}</select>
      </div>
      <div class="table-scroll">
        <table class="tx-table" id="tx-table">
          <thead>
            <tr>
              <th data-type="text">Date</th>
              <th data-type="text">Counterparty</th>
              <th data-type="text">Category</th>
              <th data-type="number" class="num">Amount</th>
              <th data-type="text">Currency</th>
            </tr>
          </thead>
          <tbody>{rows}
          </tbody>
        </table>
      </div>
    </div>
    <script>
      (function () {{
        var table = document.getElementById("tx-table");
        if (!table) return;
        var categoryFilter = document.getElementById("tx-category-filter");
        if (categoryFilter) {{
          categoryFilter.addEventListener("change", function () {{
            var selected = categoryFilter.value;
            var rows = table.querySelectorAll("tbody tr");
            rows.forEach(function (row) {{
              var category = row.children[2].textContent;
              row.style.display = !selected || category === selected ? "" : "none";
            }});
          }});
        }}
        var headers = table.querySelectorAll("thead th");
        headers.forEach(function (th, index) {{
          var state = 0;
          th.addEventListener("click", function () {{
            var tbody = table.querySelector("tbody");
            var rows = Array.prototype.slice.call(tbody.querySelectorAll("tr"));
            state = state === 1 ? -1 : 1;
            headers.forEach(function (h) {{ h.classList.remove("sort-asc", "sort-desc"); }});
            th.classList.add(state === 1 ? "sort-asc" : "sort-desc");
            var type = th.getAttribute("data-type");
            rows.sort(function (a, b) {{
              var cellA = a.children[index];
              var cellB = b.children[index];
              var valA = cellA.getAttribute("data-sort") || cellA.textContent;
              var valB = cellB.getAttribute("data-sort") || cellB.textContent;
              if (type === "number") {{
                valA = parseFloat(valA);
                valB = parseFloat(valB);
              }}
              if (valA < valB) return -1 * state;
              if (valA > valB) return 1 * state;
              return 0;
            }});
            rows.forEach(function (row) {{ tbody.appendChild(row); }});
          }});
        }});
      }})();
    </script>"""


def render_report(transactions: list[Transaction]) -> str:
    """Render a self-contained HTML report of 30-day average spend per category."""
    outgoing = [
        t for t in transactions if t.amount < 0 and t.category not in IGNORED_CATEGORIES
    ]

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

    body += _render_transactions_table(
        sorted(transactions, key=lambda t: t.date, reverse=True)
    )

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
  .table-wrap {{
    margin-top: 2rem;
    border: 1px solid var(--gridline);
    border-radius: 6px;
  }}
  .table-controls {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.85rem;
    padding: 0.6rem 0.75rem;
    border-bottom: 1px solid var(--gridline);
  }}
  .table-controls label {{ color: var(--text-secondary); }}
  .table-controls select {{
    font: inherit;
    color: var(--text-primary);
    background: var(--surface-1);
    border: 1px solid var(--gridline);
    border-radius: 4px;
    padding: 0.3rem 0.5rem;
  }}
  .table-scroll {{
    max-height: 420px;
    overflow-y: auto;
    overflow-x: auto;
  }}
  .tx-table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 0.85rem;
  }}
  .tx-table th, .tx-table td {{
    padding: 0.5rem 0.75rem;
    text-align: left;
    white-space: nowrap;
  }}
  .tx-table td.num, .tx-table th.num {{
    text-align: right;
    font-variant-numeric: tabular-nums;
  }}
  .tx-table thead th {{
    position: sticky;
    top: 0;
    background: var(--surface-1);
    color: var(--text-secondary);
    cursor: pointer;
    user-select: none;
    border-bottom: 1px solid var(--gridline);
  }}
  .tx-table thead th:hover {{ color: var(--text-primary); }}
  .tx-table thead th.sort-asc::after {{ content: " \\2191"; }}
  .tx-table thead th.sort-desc::after {{ content: " \\2193"; }}
  .tx-table tbody tr:not(:last-child) td {{ border-bottom: 1px solid var(--gridline); }}
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

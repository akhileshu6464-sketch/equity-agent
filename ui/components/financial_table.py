"""
Financial Table Component.
Level 5 visual hierarchy: Multi-year P&L, Quarterly results, Cash flow conversion flow,
and Peer comparison tables.
"""

from typing import List, Dict, Any, Optional
import streamlit as st


def render_pl_table(pl_rows: List[Dict[str, Any]]):
    """Renders multi-year annual Profit & Loss table."""
    valid_rows = [r for r in pl_rows if not (r.get("sales", 0.0) == 0.0 and r.get("net_profit", 0.0) == 0.0)]
    if not valid_rows:
        st.info("Historical multi-year financial statements not available.")
        return

    years = [str(r.get("year", "")) for r in valid_rows]
    metrics_def = [
        ("Sales", "sales", False, False),
        ("Expenses", "expenses", False, False),
        ("Operating Profit (EBITDA)", "op_profit", False, True),
        ("OPM %", "opm_pct", True, False),
        ("Other Income", "other_income", False, False),
        ("Interest", "interest", False, False),
        ("Depreciation", "depreciation", False, False),
        ("Profit before tax", "pbt", False, False),
        ("Net Profit", "net_profit", False, True),
        ("EPS in Rs", "eps", False, False),
    ]

    header_cols = "".join([f"<th>{y}</th>" for y in years])
    rows_html = []

    for label, key, is_pct, is_hl in metrics_def:
        row_cls = "highlight-row" if is_hl else ""
        cells = [f"<td>{label}</td>"]
        for r in valid_rows:
            val = r.get(key, 0.0)
            if is_pct:
                txt = f"{val:.1f}%"
            elif key == "eps":
                txt = f"{val:,.2f}"
            else:
                txt = f"{val:,.1f}"
            cells.append(f"<td>{txt}</td>")
        rows_html.append(f'<tr class="{row_cls}">{"".join(cells)}</tr>')

    html = f"""<div class="rb-table-wrap">
<table class="rb-table">
<thead>
<tr>
<th>Line Item (₹ Cr)</th>
{header_cols}
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>"""
    st.html(html)


def render_quarterly_table(q_rows: List[Dict[str, Any]]):
    """Renders quarterly financial results table."""
    if not q_rows:
        st.info("Quarterly financial records not available.")
        return

    quarters = [str(r.get("quarter", "")) for r in q_rows]
    metrics_def = [
        ("Sales", "sales", False, False),
        ("Expenses", "expenses", False, False),
        ("Operating Profit", "op_profit", False, True),
        ("OPM %", "opm_pct", True, False),
        ("Other Income", "other_income", False, False),
        ("Interest", "interest", False, False),
        ("Depreciation", "depreciation", False, False),
        ("Profit before tax", "pbt", False, False),
        ("Net Profit", "net_profit", False, True),
        ("EPS in Rs", "eps", False, False),
    ]

    header_cols = "".join([f"<th>{q}</th>" for q in quarters])
    rows_html = []

    for label, key, is_pct, is_hl in metrics_def:
        row_cls = "highlight-row" if is_hl else ""
        cells = [f"<td>{label}</td>"]
        for r in q_rows:
            val = r.get(key, 0.0)
            if is_pct:
                txt = f"{val:.1f}%"
            elif key == "eps":
                txt = f"{val:,.2f}"
            else:
                txt = f"{val:,.1f}"
            cells.append(f"<td>{txt}</td>")
        rows_html.append(f'<tr class="{row_cls}">{"".join(cells)}</tr>')

    html = f"""<div class="rb-table-wrap">
<table class="rb-table">
<thead>
<tr>
<th>Quarterly Metric (₹ Cr)</th>
{header_cols}
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>"""
    st.html(html)


def render_peer_table(peer_rows: List[Dict[str, Any]], target_symbol: str = ""):
    """Renders peer comparison table with target company clearly distinguished."""
    if not peer_rows:
        st.info("Peer benchmark data not available.")
        return

    rows_html = []
    for r in peer_rows:
        is_target = r.get("is_target", False)
        name = r.get("name", "")
        if target_symbol and target_symbol.upper() in name.upper():
            is_target = True

        row_cls = "target-row" if is_target else ""
        target_badge = ' <span style="font-size: 0.7rem; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.35); padding: 1px 5px; border-radius: 3px;">[TARGET]</span>' if is_target else ""

        cmp_txt = f"₹{r.get('cmp', 0.0):,.1f}" if r.get('cmp', 0.0) > 0 else "—"
        pe_txt = f"{r.get('pe', 0.0):.1f}x" if r.get('pe', 0.0) > 0 else "—"
        mcap_txt = f"₹{r.get('mcap_cr', 0.0):,.1f}"
        div_txt = f"{r.get('div_yield', 0.0):.2f}%" if r.get('div_yield', 0.0) > 0 else "0.00%"
        roce_txt = f"{r.get('roce', 0.0):.1f}%" if r.get('roce', 0.0) > 0 else "—"
        roe_txt = f"{r.get('roe', 0.0):.1f}%" if r.get('roe', 0.0) > 0 else "—"
        de_txt = f"{r.get('de', 0.0):.2f}" if r.get('de') is not None else "—"

        rows_html.append(f"""<tr class="{row_cls}">
<td><strong>{name}</strong>{target_badge}</td>
<td>{cmp_txt}</td>
<td>{pe_txt}</td>
<td>{mcap_txt}</td>
<td>{div_txt}</td>
<td>{roce_txt}</td>
<td>{roe_txt}</td>
<td>{de_txt}</td>
</tr>""")

    html = f"""<div class="rb-table-wrap">
<table class="rb-table">
<thead>
<tr>
<th>Company Benchmark</th>
<th>CMP</th>
<th>P/E</th>
<th>Mar Cap (₹ Cr)</th>
<th>Div Yld</th>
<th>ROCE</th>
<th>ROE</th>
<th>D/E</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>"""
    st.html(html)


def render_cash_flow_waterfall(fq_data: Dict[str, Any]):
    """Renders 5-year cumulative cash flow conversion waterfall."""
    if not fq_data:
        return

    c_pat = fq_data.get("cumulative_5y_pat", 0.0)
    c_cfo = fq_data.get("cumulative_5y_cfo", 0.0)
    c_capex = fq_data.get("cumulative_5y_capex", 0.0)
    c_fcf = fq_data.get("cumulative_5y_fcf", 0.0)
    ratio = fq_data.get("cash_conversion_ratio", 0.0)
    verdict = fq_data.get("cash_conversion_quality", "AVERAGE")

    v_color = "#34d399" if verdict in ["HIGH", "EXCELLENT"] else ("#f87171" if verdict in ["POOR", "WEAK"] else "#fbbf24")

    html = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem; margin-bottom: 1.25rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 8px;">
<span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">5-Year Cash Flow Conversion Waterfall</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; color: {v_color}; background: {v_color}18; border: 1px solid {v_color}44; padding: 2px 8px; border-radius: 4px;">
QUALITY: [{verdict}] · {ratio:.0f}% CFO/PAT
</span>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.5rem;">
<div style="background: #141f36; padding: 0.6rem 0.8rem; border-radius: 4px;">
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">5Y Cumulative PAT</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: #f8fafc;">₹{c_pat:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.6rem 0.8rem; border-radius: 4px;">
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">5Y Operating Cash Flow</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: #34d399;">₹{c_cfo:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.6rem 0.8rem; border-radius: 4px;">
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">5Y Total Capex</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: #cbd5e1;">₹{c_capex:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.6rem 0.8rem; border-radius: 4px;">
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase;">5Y Free Cash Flow</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: {'#34d399' if c_fcf >= 0 else '#f87171'};">₹{c_fcf:,.1f} Cr</div>
</div>
</div>
</div>"""
    st.html(html)

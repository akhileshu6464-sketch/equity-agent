"""
Metric Grid Component.
Renders Key Investment Signals (Revenue, EBITDA, Margin, ROCE, ROE, OCF, Debt, FCF)
in a compact, spacious, and modern multi-column grid.
"""

from typing import Dict, Any, List
import streamlit as st
from ui.components.metric_card import render_metric_card_html


def render_key_investment_signals(data: Dict[str, Any]):
    """Renders the core 8 investment signals as requested in Phase 6."""
    if not data:
        return

    pl_rows = data.get("pl_rows", [])
    latest_pl = pl_rows[-1] if pl_rows else {}

    rev = latest_pl.get("sales", 0.0)
    ebitda = latest_pl.get("op_profit", 0.0)
    opm = latest_pl.get("opm_pct", data.get("opm_pct", 0.0))
    roce = data.get("roce_pct", 0.0)
    roe = data.get("roe_pct", 0.0)
    debt = data.get("total_debt_cr", 0.0)
    cash = data.get("total_cash_cr", 0.0)
    cfo = data.get("cfo_5y_cr", 0.0)
    fcf = data.get("free_cash_flow_cr", 0.0)

    # Format values
    rev_str = f"₹{rev:,.1f} Cr" if rev > 0 else "—"
    ebitda_str = f"₹{ebitda:,.1f} Cr" if ebitda > 0 else "—"
    opm_str = f"{opm:.1f}%" if opm != 0 else "—"
    roce_str = f"{roce:.1f}%" if roce != 0 else "—"
    roe_str = f"{roe:.1f}%" if roe != 0 else "—"
    debt_str = f"₹{debt:,.1f} Cr" if debt > 0 else ("Net Cash" if cash > 0 else "₹0 Cr")
    cfo_str = f"₹{cfo:,.1f} Cr" if cfo != 0 else "—"
    fcf_str = f"₹{fcf:,.1f} Cr" if fcf != 0 else "—"

    # Status / sub-labels
    roce_sub = "Target > 15%" if roce >= 15 else "Below hurdle"
    roce_col = "#34d399" if roce >= 15 else "#94a3b8"

    roe_sub = "High return" if roe >= 15 else ""
    roe_col = "#34d399" if roe >= 15 else "#94a3b8"

    debt_sub = "Net Cash positive" if cash > debt else f"D/E {data.get('debt_to_equity', 0.0):.2f}x"
    debt_col = "#34d399" if cash > debt else "#94a3b8"

    cards = [
        render_metric_card_html("Revenue (TTM)", rev_str, "Latest annual sales"),
        render_metric_card_html("EBITDA", ebitda_str, "Operating Profit"),
        render_metric_card_html("EBITDA Margin", opm_str, "OPM %", "#38bdf8", accent=True),
        render_metric_card_html("ROCE", roce_str, roce_sub, roce_col),
        render_metric_card_html("ROE", roe_str, roe_sub, roe_col),
        render_metric_card_html("Operating Cash Flow", cfo_str, "5Y Cumulative CFO"),
        render_metric_card_html("Total Debt", debt_str, debt_sub, debt_col),
        render_metric_card_html("Free Cash Flow", fcf_str, "5Y Cumulative FCF", "#34d399" if fcf > 0 else "#f87171"),
    ]

    html = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.65rem; margin-bottom: 1.5rem;">
{"".join(cards)}
</div>"""
    st.html(html)


def render_compounded_growth_cards(data: Dict[str, Any]):
    """Renders Sales & Profit CAGR in compact cards."""
    s_3y = data.get("sales_cagr_3y")
    s_5y = data.get("sales_cagr_5y")
    p_3y = data.get("profit_cagr_3y")
    p_5y = data.get("profit_cagr_5y")

    def fmt_cagr(val):
        if val is None:
            return "N/A", "#94a3b8"
        col = "#34d399" if val >= 0 else "#f87171"
        return f"{val:+.1f}%", col

    s5_str, s5_col = fmt_cagr(s_5y)
    s3_str, s3_col = fmt_cagr(s_3y)
    p5_str, p5_col = fmt_cagr(p_5y)
    p3_str, p3_col = fmt_cagr(p_3y)

    html = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem;">
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.76rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.5rem; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">
Compounded Sales Growth
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 3px 0;">
<span style="color: #94a3b8;">5 Years CAGR:</span>
<span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: {s5_col};">{s5_str}</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 3px 0;">
<span style="color: #94a3b8;">3 Years CAGR:</span>
<span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: {s3_col};">{s3_str}</span>
</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.75rem 1rem;">
<div style="font-size: 0.76rem; color: #94a3b8; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.5rem; border-bottom: 1px solid #1e293b; padding-bottom: 4px;">
Compounded Profit Growth
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 3px 0;">
<span style="color: #94a3b8;">5 Years CAGR:</span>
<span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: {p5_col};">{p5_str}</span>
</div>
<div style="display: flex; justify-content: space-between; font-size: 0.85rem; padding: 3px 0;">
<span style="color: #94a3b8;">3 Years CAGR:</span>
<span style="font-family: 'JetBrains Mono', monospace; font-weight: 700; color: {p3_col};">{p3_str}</span>
</div>
</div>
</div>"""
    st.html(html)

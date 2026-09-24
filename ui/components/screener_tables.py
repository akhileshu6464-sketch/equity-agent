"""
Screener Tables & Layer 1 Financial Presentation (ui/components/screener_tables.py)
Implements Layer 1: Screener-Style Verified Financial Data.
Pure factual company numbers, multi-period financial tables, stock chart,
peers, and corporate filings. Zero AI hallucination or guessing.
"""

import html
import re
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from services.screener_fetcher import fetch_stock_chart_data, fetch_day_change, _parse_numeric


def _esc(text: Any) -> str:
    """Safely escapes HTML strings."""
    if text is None:
        return ""
    return html.escape(str(text))


# -------------------------------------------------------------------------
# 1. LAYER 1 HEADER
# -------------------------------------------------------------------------
def render_layer1_header(
    company_name: str,
    nse_symbol: str,
    bse_code: str,
    isin: str,
    sector: str,
    industry: str,
    market_cap_str: str,
    current_price_str: str,
    day_change_rs: float = 0.0,
    day_change_pct: float = 0.0,
):
    """
    Renders the top identity header:
    Company name, NSE symbol, BSE code, ISIN, Sector, Industry, Market Cap, Current Price, Day Change.
    """
    cname = _esc(company_name)
    nse = _esc(nse_symbol or "—")
    bse = _esc(bse_code or "—")
    isin_clean = _esc(isin or "—")
    sec = _esc(sector or "General")
    ind = _esc(industry or "Diversified")
    cmp_str = _esc(current_price_str)
    mcap_str = _esc(market_cap_str)

    if day_change_rs > 0:
        chg_color = "#34d399"
        chg_bg = "rgba(52, 211, 153, 0.12)"
        chg_sign = "+"
        chg_arrow = "▲"
    elif day_change_rs < 0:
        chg_color = "#f87171"
        chg_bg = "rgba(248, 113, 113, 0.15)"
        chg_sign = ""
        chg_arrow = "▼"
    else:
        chg_color = "#94a3b8"
        chg_bg = "rgba(148, 163, 184, 0.12)"
        chg_sign = ""
        chg_arrow = "■"

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1rem;">
<div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
  <div>
    <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.4rem; flex-wrap: wrap;">
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.3); padding: 2px 8px; border-radius: 4px;">NSE: {nse}</span>
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; font-weight: 600; color: #94a3b8; background: #141f36; border: 1px solid #1e293b; padding: 2px 8px; border-radius: 4px;">BSE: {bse}</span>
      <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #64748b;">ISIN: {isin_clean}</span>
      <span style="font-size: 0.72rem; color: #34d399; font-weight: 600; display: inline-flex; align-items: center; gap: 4px;">
        <span style="width: 6px; height: 6px; border-radius: 50%; background: #34d399; display: inline-block;"></span> Verified Database
      </span>
    </div>
    <div style="font-size: 1.85rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.02em; line-height: 1.2; margin-bottom: 0.25rem;">
      {cname}
    </div>
    <div style="font-size: 0.84rem; color: #94a3b8;">
      <span>📂 {sec}</span> &nbsp;•&nbsp; <span>🏭 {ind}</span>
    </div>
  </div>
  <div style="display: flex; gap: 2rem; align-items: flex-end; flex-wrap: wrap;">
    <div>
      <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 2px;">Current Price</div>
      <div style="display: flex; align-items: baseline; gap: 0.6rem;">
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 1.65rem; color: #f8fafc; font-weight: 800;">{cmp_str}</span>
        <span style="font-family: 'JetBrains Mono', monospace; font-size: 0.82rem; font-weight: 700; color: {chg_color}; background: {chg_bg}; border: 1px solid {chg_color}44; padding: 2px 6px; border-radius: 4px;">
          {chg_arrow} {chg_sign}{day_change_rs:,.2f} ({chg_sign}{day_change_pct:+.2f}%)
        </span>
      </div>
    </div>
    <div>
      <div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 2px;">Market Cap</div>
      <div style="font-family: 'JetBrains Mono', monospace; font-size: 1.65rem; color: #38bdf8; font-weight: 800;">{mcap_str}</div>
    </div>
  </div>
</div>
</div>""")


# -------------------------------------------------------------------------
# 2. HORIZONTAL NAVIGATION
# -------------------------------------------------------------------------
def render_horizontal_nav():
    """
    Renders clean horizontal navigation with fast jump anchors:
    Overview, Financials, Quarterly, Annual, Cash Flow, Balance Sheet, Ratios, Peers, Shareholding, Charts, News, Analysis.
    """
    nav_items = [
        ("Overview", "#overview"),
        ("Financials", "#financials"),
        ("Quarterly", "#quarterly"),
        ("Annual", "#annual"),
        ("Cash Flow", "#cash-flow"),
        ("Balance Sheet", "#balance-sheet"),
        ("Ratios", "#ratios"),
        ("Peers", "#peers"),
        ("Shareholding", "#shareholding"),
        ("Charts", "#chart"),
        ("News", "#news"),
        ("🧠 Analysis", "#analysis"),
    ]

    pills_html = []
    for label, anchor in nav_items:
        is_analysis = anchor == "#analysis"
        if is_analysis:
            pills_html.append(
                f'<a href="{anchor}" style="text-decoration: none; color: #38bdf8; background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; font-weight: 700; transition: all 0.15s ease;">{label}</a>'
            )
        else:
            pills_html.append(
                f'<a href="{anchor}" style="text-decoration: none; color: #cbd5e1; background: #141f36; border: 1px solid #1e293b; padding: 5px 12px; border-radius: 6px; font-size: 0.82rem; font-weight: 500; transition: all 0.15s ease;">{label}</a>'
            )

    st.html(f"""<div style="position: sticky; top: 0; z-index: 99; background: #0b0f19; border-bottom: 1px solid #1e293b; padding: 0.65rem 0; margin-bottom: 1.25rem; display: flex; gap: 0.45rem; overflow-x: auto; white-space: nowrap;">
{"".join(pills_html)}
</div>""")


# -------------------------------------------------------------------------
# 3. OVERVIEW ROW (Clean Typography, No Excessive Boxes)
# -------------------------------------------------------------------------
def render_overview_row(ratios: Dict[str, Any], debt_to_equity: Optional[float] = None):
    """
    Shows essential company numbers in a clean, compact horizontal stats row:
    Market Cap | P/E | P/B | ROE | ROCE | Debt / Equity | Dividend Yield | Face Value
    """
    st.html('<div id="overview"></div>')

    mcap = ratios.get("Market Cap", "—")
    pe = ratios.get("Stock P/E", "—")
    bv = ratios.get("Book Value", "—")
    roe = ratios.get("ROE", "—")
    roce = ratios.get("ROCE", "—")
    div = ratios.get("Dividend Yield", "—")
    fv = ratios.get("Face Value", "—")

    # Parse P/B if current price and book value available
    pb_str = "—"
    cmp_num = ratios.get("current_price")
    bv_num = ratios.get("book_value")
    if cmp_num and bv_num and bv_num > 0:
        pb_str = f"{cmp_num / bv_num:.2f}"

    # Debt to Equity
    de_str = f"{debt_to_equity:.2f}" if debt_to_equity is not None else "—"

    metrics = [
        ("Market Cap", mcap, "#38bdf8"),
        ("Stock P/E", pe, "#fbbf24" if pe != "—" else "#f8fafc"),
        ("Price to Book", pb_str, "#f8fafc"),
        ("ROE", roe, "#38bdf8" if roe != "—" else "#f8fafc"),
        ("ROCE", roce, "#34d399" if roce != "—" else "#f8fafc"),
        ("Debt / Equity", de_str, "#34d399" if de_str != "—" and debt_to_equity < 0.5 else "#f8fafc"),
        ("Dividend Yield", div, "#f8fafc"),
        ("Face Value", fv, "#f8fafc"),
    ]

    cells = []
    for lbl, val, col in metrics:
        cells.append(f"""<div style="flex: 1 1 110px; min-width: 100px; padding: 0.65rem 0.85rem; border-right: 1px solid #1e293b;">
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em; margin-bottom: 2px;">{lbl}</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.05rem; font-weight: 700; color: {col};">{_esc(val)}</div>
</div>""")

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; display: flex; flex-wrap: wrap; margin-bottom: 1.5rem; overflow: hidden;">
{"".join(cells)}
</div>""")


# -------------------------------------------------------------------------
# 4. STOCK CHART
# -------------------------------------------------------------------------
def render_stock_chart(symbol: str):
    """
    Renders clean stock price and volume chart with time controls:
    1M, 6M, 1Y, 3Y, 5Y, MAX.
    """
    st.html('<div id="chart"></div>')
    st.markdown("### 📈 Stock Price & Volume")

    col_tf, _ = st.columns([3, 5])
    with col_tf:
        tf = st.segmented_control(
            "Timeframe",
            options=["1M", "6M", "1Y", "3Y", "5Y", "MAX"],
            default="1Y",
            label_visibility="collapsed",
            key=f"stock_chart_tf_{symbol}"
        ) or "1Y"

    with st.spinner("Fetching market trading history..."):
        df = fetch_stock_chart_data(symbol, timeframe=tf)

    if df.empty or len(df) < 2:
        st.info("Market trading history currently unavailable for this ticker.")
        return

    # Create 2-row subplot: Price on top, Volume on bottom
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.04,
        row_heights=[0.75, 0.25]
    )

    # Price Line + Gradient Area
    is_positive = df["Close"].iloc[-1] >= df["Close"].iloc[0]
    line_color = "#34d399" if is_positive else "#f87171"
    fill_color = "rgba(52, 211, 153, 0.08)" if is_positive else "rgba(248, 113, 113, 0.08)"

    fig.add_trace(
        go.Scatter(
            x=df["Date"],
            y=df["Close"],
            mode="lines",
            name="Close Price",
            line=dict(color=line_color, width=2),
            fill="tozeroy",
            fillcolor=fill_color,
            hovertemplate="<b>Date:</b> %{x|%d %b %Y}<br><b>Price:</b> ₹%{y:,.2f}<extra></extra>"
        ),
        row=1,
        col=1
    )

    # Volume Bars
    vol_color = "rgba(52, 211, 153, 0.35)" if is_positive else "rgba(248, 113, 113, 0.35)"
    fig.add_trace(
        go.Bar(
            x=df["Date"],
            y=df["Volume"],
            name="Volume",
            marker=dict(color=vol_color),
            hovertemplate="<b>Volume:</b> %{y:,.0f}<extra></extra>"
        ),
        row=2,
        col=1
    )

    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0b0f19",
        margin=dict(l=10, r=10, t=10, b=10),
        height=380,
        showlegend=False,
        hovermode="x unified",
        xaxis=dict(showgrid=True, gridcolor="#1e293b", showline=False),
        yaxis=dict(showgrid=True, gridcolor="#1e293b", showline=False, side="right", tickprefix="₹"),
        xaxis2=dict(showgrid=False, showline=False),
        yaxis2=dict(showgrid=False, showline=False, side="right"),
    )

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# -------------------------------------------------------------------------
# 5. KEY FINANCIALS (Quarterly | Annual Switcher)
# -------------------------------------------------------------------------
def render_compact_key_financials(pl_df: pd.DataFrame, quarters_df: pd.DataFrame):
    """
    Renders compact table showing:
    Revenue, EBITDA, EBITDA Margin, PAT, EPS.
    Switcher: Quarterly | Annual.
    """
    st.html('<div id="financials"></div>')
    st.markdown("### 📋 Key Financials")

    mode = st.segmented_control(
        "Financial Horizon",
        options=["Annual", "Quarterly"],
        default="Annual",
        label_visibility="collapsed",
        key="key_fin_mode_toggle"
    ) or "Annual"

    source_df = pl_df if mode == "Annual" else quarters_df
    if source_df is None or source_df.empty:
        st.info(f"Verified {mode} financial statements not available in extract.")
        return

    # Filter or map to Revenue, EBITDA, EBITDA Margin, PAT, EPS
    target_metrics = {
        "Sales": "Revenue (₹ Cr)",
        "Revenue": "Revenue (₹ Cr)",
        "Operating Profit": "EBITDA (₹ Cr)",
        "OPM %": "EBITDA Margin (%)",
        "Net Profit": "PAT (₹ Cr)",
        "EPS in Rs": "EPS (₹)",
    }

    filtered_rows = []
    period_cols = [c for c in source_df.columns if c != "Metric"]

    for _, row in source_df.iterrows():
        raw_m = str(row.get("Metric", "")).strip()
        matched_label = None
        for k, label in target_metrics.items():
            if k.lower() == raw_m.lower() or raw_m.lower().startswith(k.lower()):
                matched_label = label
                break
        if matched_label and not any(r["Metric"] == matched_label for r in filtered_rows):
            new_row = {"Metric": matched_label}
            for col in period_cols:
                new_row[col] = row.get(col, "—")
            filtered_rows.append(new_row)

    if filtered_rows:
        display_df = pd.DataFrame(filtered_rows)
        # Take up to last 8 periods for clean readability
        display_cols = ["Metric"] + period_cols[-8:]
        display_df = display_df[[c for c in display_cols if c in display_df.columns]]
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        # Fallback to source_df
        st.dataframe(source_df.head(6), use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 6. PEERS COMPARISON TABLE (Pure Real Data, Highlight Target)
# -------------------------------------------------------------------------
def render_peers_table(peer_rows: List[Dict[str, Any]], target_symbol: str):
    """
    Renders pure verified peer comparison table:
    Company | Market Cap | P/E | ROE | ROCE.
    Highlight the current company. Zero AI guessing.
    """
    st.html('<div id="peers"></div>')
    st.markdown("### 👥 Peer Comparison")
    st.caption("Sector benchmark peers from verified exchange data. Primary company highlighted.")

    if not peer_rows:
        st.info("No verified peer comparison data available for this sector.")
        return

    rows_html = []
    clean_target = (target_symbol or "").upper().replace(".NS", "").replace(".BO", "")

    for p in peer_rows:
        p_name = p.get("name") or p.get("company_name") or p.get("symbol") or "Peer Enterprise"
        p_sym = str(p.get("symbol") or "").upper().replace(".NS", "").replace(".BO", "")
        mcap = p.get("market_cap_cr") or p.get("market_cap") or "—"
        pe = p.get("pe_ratio") or p.get("pe") or "—"
        roe = p.get("roe") or p.get("roe_pct") or "—"
        roce = p.get("roce") or p.get("roce_pct") or "—"
        is_target = p.get("is_target", False) or (clean_target and clean_target == p_sym)

        mcap_str = f"₹{mcap:,.1f} Cr" if isinstance(mcap, (int, float)) and mcap > 0 else str(mcap)
        pe_str = f"{pe:.1f}x" if isinstance(pe, (int, float)) and pe > 0 else str(pe)
        roe_str = f"{roe:.1f}%" if isinstance(roe, (int, float)) and roe > 0 else str(roe)
        roce_str = f"{roce:.1f}%" if isinstance(roce, (int, float)) and roce > 0 else str(roce)

        if is_target:
            row_style = "background: rgba(56, 189, 248, 0.12); font-weight: 700; border-left: 3px solid #38bdf8;"
            badge = " <span style='font-size: 0.72rem; color: #38bdf8; background: #0f172a; padding: 1px 6px; border-radius: 3px; border: 1px solid rgba(56,189,248,0.4);'>Current</span>"
        else:
            row_style = "border-bottom: 1px solid #1e293b;"
            badge = ""

        rows_html.append(f"""<tr style="{row_style}">
<td style="padding: 0.65rem 0.85rem; color: #f8fafc;">{_esc(p_name)}{badge}</td>
<td style="padding: 0.65rem 0.85rem; text-align: right; font-family: 'JetBrains Mono', monospace; color: #cbd5e1;">{mcap_str}</td>
<td style="padding: 0.65rem 0.85rem; text-align: right; font-family: 'JetBrains Mono', monospace; color: #cbd5e1;">{pe_str}</td>
<td style="padding: 0.65rem 0.85rem; text-align: right; font-family: 'JetBrains Mono', monospace; color: #38bdf8;">{roe_str}</td>
<td style="padding: 0.65rem 0.85rem; text-align: right; font-family: 'JetBrains Mono', monospace; color: #34d399;">{roce_str}</td>
</tr>""")

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; overflow-x: auto; margin-bottom: 1.5rem;">
<table style="width: 100%; border-collapse: collapse; font-size: 0.88rem;">
<thead>
<tr style="border-bottom: 1px solid #334155; background: #141f36; text-transform: uppercase; font-size: 0.72rem; letter-spacing: 0.04em; color: #94a3b8;">
  <th style="padding: 0.65rem 0.85rem; text-align: left;">Company</th>
  <th style="padding: 0.65rem 0.85rem; text-align: right;">Market Cap</th>
  <th style="padding: 0.65rem 0.85rem; text-align: right;">P/E</th>
  <th style="padding: 0.65rem 0.85rem; text-align: right;">ROE</th>
  <th style="padding: 0.65rem 0.85rem; text-align: right;">ROCE</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>""")


# -------------------------------------------------------------------------
# 7. QUARTERLY P&L (Visual Chart + Table)
# -------------------------------------------------------------------------
def render_quarterly_section(quarters_df: pd.DataFrame):
    """
    Renders Quarterly P&L:
    Revenue, EBITDA, PAT across recent quarters with visual chart + table.
    """
    st.html('<div id="quarterly"></div>')
    st.markdown("### 📊 Quarterly Results (₹ Crores)")

    if quarters_df is None or quarters_df.empty:
        st.info("No quarterly results table available in current disclosures.")
        return

    # Extract Revenue, Operating Profit (EBITDA), Net Profit (PAT)
    cols = [c for c in quarters_df.columns if c != "Metric"]
    sales_row = quarters_df[quarters_df["Metric"].str.startswith("Sales", na=False)]
    op_row = quarters_df[quarters_df["Metric"].str.startswith("Operating Profit", na=False)]
    np_row = quarters_df[quarters_df["Metric"].str.startswith("Net Profit", na=False)]

    if not sales_row.empty and len(cols) >= 3:
        # Build Visual Chart for last 8 quarters
        chart_cols = cols[-8:]
        rev_vals = [_parse_numeric(str(sales_row[c].iloc[0])) or 0.0 for c in chart_cols]
        op_vals = [_parse_numeric(str(op_row[c].iloc[0])) or 0.0 for c in chart_cols] if not op_row.empty else []
        pat_vals = [_parse_numeric(str(np_row[c].iloc[0])) or 0.0 for c in chart_cols] if not np_row.empty else []

        fig = go.Figure()
        fig.add_trace(go.Bar(x=chart_cols, y=rev_vals, name="Revenue", marker_color="#38bdf8"))
        if op_vals:
            fig.add_trace(go.Bar(x=chart_cols, y=op_vals, name="EBITDA", marker_color="#818cf8"))
        if pat_vals:
            fig.add_trace(go.Bar(x=chart_cols, y=pat_vals, name="PAT", marker_color="#34d399"))

        fig.update_layout(
            barmode="group",
            template="plotly_dark",
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            margin=dict(l=10, r=10, t=10, b=10),
            height=260,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e293b", tickprefix="₹"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Render Full Table
    st.dataframe(quarters_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 8. 10-YEAR ANNUAL FINANCIALS (Chart Switcher + Table)
# -------------------------------------------------------------------------
def render_annual_section(pl_df: pd.DataFrame):
    """
    Renders 10-Year Annual Financials:
    Long-term view of Revenue, EBITDA, PAT with chart switcher (Revenue | Operating Profit | Net Profit).
    """
    st.html('<div id="annual"></div>')
    st.markdown("### 🏛️ 10-Year Annual Financials (₹ Crores)")

    if pl_df is None or pl_df.empty:
        st.info("No 10-year Profit & Loss table available in current disclosures.")
        return

    cols = [c for c in pl_df.columns if c != "Metric"]

    # Visual Chart Switcher
    col_sw, _ = st.columns([3, 5])
    with col_sw:
        metric_choice = st.segmented_control(
            "Chart Metric",
            options=["Revenue", "Operating Profit", "Net Profit"],
            default="Revenue",
            label_visibility="collapsed",
            key="annual_chart_metric_toggle"
        ) or "Revenue"

    metric_prefix = {
        "Revenue": "Sales",
        "Operating Profit": "Operating Profit",
        "Net Profit": "Net Profit",
    }[metric_choice]

    row_match = pl_df[pl_df["Metric"].str.startswith(metric_prefix, na=False)]
    if not row_match.empty and cols:
        vals = [_parse_numeric(str(row_match[c].iloc[0])) or 0.0 for c in cols]
        chart_color = "#38bdf8" if metric_choice == "Revenue" else ("#818cf8" if metric_choice == "Operating Profit" else "#34d399")

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cols,
            y=vals,
            name=metric_choice,
            marker_color=chart_color,
            hovertemplate="<b>Year:</b> %{x}<br><b>Amount:</b> ₹%{y:,.1f} Cr<extra></extra>"
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            margin=dict(l=10, r=10, t=10, b=10),
            height=250,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e293b", tickprefix="₹"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # Render Full 10-Year Table
    st.dataframe(pl_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 9. CASH FLOW (Visual Chart + Table)
# -------------------------------------------------------------------------
def render_cash_flow_section(cf_df: pd.DataFrame):
    """
    Renders Cash Flow:
    Operating, Investing, Financing, and Net Cash Flow (visual chart + table).
    """
    st.html('<div id="cash-flow"></div>')
    st.markdown("### 💸 Cash Flow Statement (₹ Crores)")

    if cf_df is None or cf_df.empty:
        st.info("No Cash Flow table available in current disclosures.")
        return

    cols = [c for c in cf_df.columns if c != "Metric"]
    cfo_row = cf_df[cf_df["Metric"].str.contains("Operating", case=False, na=False)]

    if not cfo_row.empty and cols:
        cfo_vals = [_parse_numeric(str(cfo_row[c].iloc[0])) or 0.0 for c in cols]
        colors = ["#34d399" if v >= 0 else "#f87171" for v in cfo_vals]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=cols,
            y=cfo_vals,
            name="Operating Cash Flow",
            marker_color=colors,
            hovertemplate="<b>Year:</b> %{x}<br><b>CFO:</b> ₹%{y:,.1f} Cr<extra></extra>"
        ))
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#0b0f19",
            plot_bgcolor="#0b0f19",
            margin=dict(l=10, r=10, t=10, b=10),
            height=240,
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=True, gridcolor="#1e293b", tickprefix="₹"),
        )
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.dataframe(cf_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 10. BALANCE SHEET
# -------------------------------------------------------------------------
def render_balance_sheet_section(bs_df: pd.DataFrame):
    """
    Renders Balance Sheet:
    Assets, Liabilities, Equity, Debt, Cash historical comparison.
    """
    st.html('<div id="balance-sheet"></div>')
    st.markdown("### ⚖️ Balance Sheet (₹ Crores)")

    if bs_df is None or bs_df.empty:
        st.info("No Balance Sheet table available in current disclosures.")
        return

    st.dataframe(bs_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 11. RATIO ANALYSIS
# -------------------------------------------------------------------------
def render_ratios_section(ratios_df: pd.DataFrame):
    """
    Renders Ratio Analysis:
    ROE, ROCE, Debtor Days, Inventory Days, Working Capital Days, Cash Conversion Cycle trend over time.
    """
    st.html('<div id="ratios"></div>')
    st.markdown("### 📐 Key Financial & Efficiency Ratios")

    if ratios_df is None or ratios_df.empty:
        st.info("No historical Ratios table available in current disclosures.")
        return

    st.dataframe(ratios_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 12. SHAREHOLDING PATTERN
# -------------------------------------------------------------------------
def render_shareholding_section(sh_df: pd.DataFrame):
    """
    Renders Shareholding:
    Promoters, FII, DII, Public, Other historical changes across quarters.
    """
    st.html('<div id="shareholding"></div>')
    st.markdown("### 🤝 Shareholding Pattern (%)")

    if sh_df is None or sh_df.empty:
        st.info("No Shareholding Pattern table available in current disclosures.")
        return

    cols = [c for c in sh_df.columns if c != "Metric"]
    if len(cols) >= 2:
        # Stacked area chart of shareholding categories
        fig = go.Figure()
        palette = {
            "Promoters": "#38bdf8",
            "FII": "#818cf8",
            "DII": "#fbbf24",
            "Public": "#34d399",
            "Others": "#94a3b8"
        }
        for _, row in sh_df.iterrows():
            m_name = str(row.get("Metric", "")).strip()
            # Match category
            matched_key = None
            for pk in palette:
                if pk.lower() in m_name.lower():
                    matched_key = pk
                    break
            if matched_key:
                vals = [_parse_numeric(str(row.get(c, "0")).replace("%", "")) or 0.0 for c in cols]
                fig.add_trace(go.Scatter(
                    x=cols,
                    y=vals,
                    name=matched_key,
                    mode="lines",
                    stackgroup="one",
                    line=dict(width=1, color=palette[matched_key]),
                    hovertemplate=f"<b>{matched_key}:</b> %{{y:.2f}}%<extra></extra>"
                ))

        if len(fig.data) > 0:
            fig.update_layout(
                template="plotly_dark",
                paper_bgcolor="#0b0f19",
                plot_bgcolor="#0b0f19",
                margin=dict(l=10, r=10, t=10, b=10),
                height=260,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                xaxis=dict(showgrid=False),
                yaxis=dict(showgrid=True, gridcolor="#1e293b", ticksuffix="%"),
            )
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    st.dataframe(sh_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------------------
# 13. NEWS & REGULATORY ANNOUNCEMENTS
# -------------------------------------------------------------------------
def render_news_section(announcements: List[Dict[str, str]]):
    """
    Renders Recent Company News / Regulatory Filings:
    Headline, Date, Source. Neutral and factual. No AI interpretation here.
    """
    st.html('<div id="news"></div>')
    st.markdown("### 📰 Recent Company News & Regulatory Filings")
    st.caption("Direct regulatory disclosures filed with the exchange. 100% factual and uninterpreted.")

    if not announcements:
        st.info("No recent regulatory announcements filed in the current extract.")
        return

    items_html = []
    for item in announcements[:12]:
        headline = _esc(item.get("headline", "Regulatory Filing"))
        date_str = _esc(item.get("date", "Recent"))
        source = _esc(item.get("source", "BSE / Regulatory Filing"))
        link = item.get("link", "")

        link_tag = f'<a href="{link}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.78rem; font-weight: 600;">View Filing ↗</a>' if link else ""

        items_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1.15rem; margin-bottom: 0.6rem; display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap;">
  <div style="flex: 1 1 300px;">
    <div style="font-size: 0.9rem; color: #f8fafc; font-weight: 600; line-height: 1.4; margin-bottom: 4px;">{headline}</div>
    <div style="font-size: 0.76rem; color: #94a3b8; display: flex; gap: 12px;">
      <span>📅 {date_str}</span>
      <span>🏛️ {source}</span>
    </div>
  </div>
  <div>{link_tag}</div>
</div>""")

    st.html(f'<div style="margin-bottom: 1.5rem;">{"".join(items_html)}</div>')

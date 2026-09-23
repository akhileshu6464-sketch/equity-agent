"""
Company Header Component.
Level 1 visual hierarchy: Clean, modern header with company legal name, exchange ticker,
sector, current market price, market cap, and primary verification badges.
"""

from typing import Optional, Dict, Any
import streamlit as st


def render_company_header(
    company_name: str,
    symbol: str,
    sector: str = "",
    industry: str = "",
    cmp: float = 0.0,
    market_cap_cr: float = 0.0,
    high_52: float = 0.0,
    low_52: float = 0.0,
    rating: str = "",
    website: str = "",
    bse_url: str = "",
    nse_url: str = "",
):
    """Renders the top Level 1 Company Identity Header."""
    cmp_str = f"₹{cmp:,.2f}" if cmp > 0 else "—"
    mcap_str = f"₹{market_cap_cr:,.1f} Cr" if market_cap_cr > 0 else "—"
    h52_str = f"₹{high_52:,.0f}" if high_52 > 0 else "—"
    l52_str = f"₹{low_52:,.0f}" if low_52 > 0 else "—"

    sector_line = f"{symbol} · NSE"
    if sector:
        sector_line += f" · {sector}"
    if industry and industry != sector:
        sector_line += f" ({industry})"

    links = []
    if website:
        links.append(f'<a href="{website}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.8rem; font-weight: 500;">Website ↗</a>')
    if bse_url:
        links.append(f'<a href="{bse_url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.8rem; font-weight: 500;">BSE ↗</a>')
    if nse_url:
        links.append(f'<a href="{nse_url}" target="_blank" style="color: #38bdf8; text-decoration: none; font-size: 0.8rem; font-weight: 500;">NSE ↗</a>')
    links_html = f'<div style="display: flex; gap: 12px; margin-top: 6px;">{" ".join(links)}</div>' if links else ""

    rating_badge = ""
    if rating:
        rating_color = "#34d399" if any(w in rating.upper() for w in ["BUY", "ACCUMULATE"]) else ("#f87171" if any(w in rating.upper() for w in ["SELL", "REDUCE", "AVOID"]) else "#fbbf24")
        rating_badge = f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 0.75rem; font-weight: 700; color: {rating_color}; background: {rating_color}18; border: 1px solid {rating_color}44; padding: 3px 8px; border-radius: 4px;">{rating}</span>'

    html = f"""<div style="padding-bottom: 1.25rem; margin-bottom: 1rem; border-bottom: 1px solid #1e293b; display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1.5rem;">
<div style="flex: 1; min-width: 280px;">
<div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 4px;">
<h1 style="margin: 0; font-size: 1.95rem; font-weight: 700; letter-spacing: -0.025em; color: #f8fafc; line-height: 1.2;">
{company_name}
</h1>
{rating_badge}
</div>
<div style="font-size: 0.88rem; color: #94a3b8; font-weight: 500; margin-bottom: 4px;">
{sector_line}
</div>
{links_html}
</div>
<div style="display: flex; gap: 2rem; align-items: baseline; text-align: right; flex-wrap: wrap;">
<div>
<div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em; margin-bottom: 2px;">Market Cap</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{mcap_str}</div>
</div>
<div>
<div style="font-size: 0.72rem; color: #64748b; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em; margin-bottom: 2px;">Share Price</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.75rem; font-weight: 700; color: #34d399; line-height: 1.1;">{cmp_str}</div>
<div style="font-size: 0.74rem; color: #94a3b8; margin-top: 3px; font-variant-numeric: tabular-nums;">
52W: <span style="color: #cbd5e1;">{l52_str}</span> – <span style="color: #cbd5e1;">{h52_str}</span>
</div>
</div>
</div>
</div>"""
    st.html(html)

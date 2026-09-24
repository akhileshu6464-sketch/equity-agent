"""
Screener-Style Frontend View (ui/components/screener_view.py)
Renders a clean, high-conviction Screener.in style interface:
1. Top Header: Company Name, CMP, and Market Cap.
2. About Box: Authentic business summary and key operations.
3. Ratios Grid: 3x3 clean metric grid for the key ratios.
4. Financial Table: 5 to 10-year Profit & Loss table in a clean Pandas/Streamlit table.
5. Editorial Memo: LLM-generated qualitative thesis (Thesis, Moats, Risks).
"""

import html
from typing import Dict, Any, List, Optional
import streamlit as st
import pandas as pd


def _escape(text: Any) -> str:
    """Safely escapes HTML strings."""
    if text is None:
        return ""
    return html.escape(str(text))


def render_screener_top_header(
    company_name: str,
    cmp_str: str,
    mcap_str: str,
    symbol: str
):
    """
    Renders the clean Screener-style top header with Company Name, CMP, and Market Cap.
    """
    cname = _escape(company_name)
    cmp_val = _escape(cmp_str)
    mcap_val = _escape(mcap_str)
    sym = _escape(symbol)

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem 1.5rem; margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
<div>
<div style="display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.35rem;">
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.12); border: 1px solid rgba(56, 189, 248, 0.3); padding: 2px 8px; border-radius: 4px;">{sym}</span>
<span style="font-size: 0.72rem; color: #34d399; font-weight: 600; display: flex; align-items: center; gap: 4px;">
<span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #34d399;"></span> Verified Direct Screener Extract
</span>
</div>
<div style="font-size: 1.75rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em; line-height: 1.2;">{cname}</div>
</div>
<div style="display: flex; gap: 2rem; align-items: baseline; flex-wrap: wrap;">
<div>
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em;">Current Price</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: #f8fafc; font-weight: 700;">{cmp_val}</div>
</div>
<div>
<div style="font-size: 0.7rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em;">Market Cap</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.5rem; color: #38bdf8; font-weight: 700;">{mcap_val}</div>
</div>
</div>
</div>""")


def render_screener_about_box(company_name: str, about_text: str):
    """
    Renders the official business summary and key operations narrative.
    """
    cname = _escape(company_name)
    about = _escape(about_text or "Official business overview not disclosed in current extract.")

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 4px solid #38bdf8; border-radius: 8px; padding: 1.15rem 1.4rem; margin-bottom: 1.25rem;">
<div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; letter-spacing: 0.05em; margin-bottom: 0.45rem;">
🏢 About {cname}
</div>
<div style="font-size: 0.92rem; color: #cbd5e1; line-height: 1.65; font-weight: 400;">
{about}
</div>
</div>""")


def render_screener_ratios_3x3(ratios: Dict[str, Any]):
    """
    Renders a clean 3x3 metric grid for the 9 Screener key ratios:
    1. Market Cap
    2. Current Price
    3. High / Low
    4. Stock P/E
    5. Book Value
    6. Dividend Yield
    7. ROCE
    8. ROE
    9. Face Value
    """
    items = [
        ("Market Cap", ratios.get("Market Cap", "N/A")),
        ("Current Price", ratios.get("Current Price", "N/A")),
        ("High / Low", ratios.get("High / Low", "N/A")),
        ("Stock P/E", ratios.get("Stock P/E", "N/A")),
        ("Book Value", ratios.get("Book Value", "N/A")),
        ("Dividend Yield", ratios.get("Dividend Yield", "N/A")),
        ("ROCE", ratios.get("ROCE", "N/A")),
        ("ROE", ratios.get("ROE", "N/A")),
        ("Face Value", ratios.get("Face Value", "N/A")),
    ]

    cards_html = []
    for label, val in items:
        clean_lbl = _escape(label)
        clean_v = _escape(val)
        # Highlight ROCE, ROE, P/E with subtle accents
        color = "#f8fafc"
        if label == "ROCE":
            color = "#34d399"
        elif label == "ROE":
            color = "#38bdf8"
        elif label == "Stock P/E":
            color = "#fbbf24"

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1.15rem;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase; font-weight: 600; letter-spacing: 0.04em; margin-bottom: 0.25rem;">{clean_lbl}</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; color: {color}; font-weight: 700;">{clean_v}</div>
</div>""")

    st.html(f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem;">
{"".join(cards_html)}
</div>""")


def render_screener_financial_table(df: pd.DataFrame):
    """
    Renders the 5 to 10-year Profit & Loss table in a clean Streamlit dataframe.
    """
    st.subheader("📊 Profit & Loss (Consolidated · ₹ Crores)")
    st.caption("10-Year historical track record extracted directly from official regulatory disclosures.")
    if df is not None and not df.empty:
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True,
            height=min(450, 40 + len(df) * 35)
        )
    else:
        st.info("No historical Profit & Loss table available in current disclosures.")


def render_screener_editorial_memo(memo: Dict[str, Any]):
    """
    Renders the LLM-generated qualitative thesis below the tables:
    - Investment Thesis
    - Structural Moats
    - Key Risks
    """
    st.subheader("📝 Editorial Research Memo (Qualitative Analysis)")
    st.caption("LLM qualitative synthesis locked strictly to verified figures (Temperature 0.2 · Zero calculated numbers).")

    thesis = _escape(memo.get("investment_thesis", ""))
    moats = memo.get("structural_moats", [])
    risks = memo.get("key_risks", [])

    col1, col2 = st.columns(2)
    with col1:
        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #38bdf8; border-radius: 6px; padding: 1.15rem; margin-bottom: 1rem; min-height: 220px;">
<div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 0.4rem; letter-spacing: 0.04em;">🎯 Investment Thesis</div>
<div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.6;">{thesis}</div>
</div>""")

    with col2:
        moats_html = "".join([f"<li style='margin-bottom: 6px;'>{_escape(m)}</li>" for m in moats])
        st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #34d399; border-radius: 6px; padding: 1.15rem; margin-bottom: 1rem; min-height: 220px;">
<div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 0.4rem; letter-spacing: 0.04em;">🛡️ Structural Moats & Advantages</div>
<ul style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; padding-left: 1.2rem; margin: 0;">{moats_html}</ul>
</div>""")

    risks_html = "".join([f"<li style='margin-bottom: 6px;'>{_escape(r)}</li>" for r in risks])
    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #f87171; border-radius: 6px; padding: 1.15rem; margin-bottom: 1.25rem;">
<div style="font-size: 0.75rem; color: #94a3b8; text-transform: uppercase; font-weight: 700; margin-bottom: 0.4rem; letter-spacing: 0.04em;">⚠️ Key Risks & Vulnerabilities</div>
<ul style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; padding-left: 1.2rem; margin: 0;">{risks_html}</ul>
</div>""")

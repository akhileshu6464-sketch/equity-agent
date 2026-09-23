"""
Business Health & Executive Decision Matrix Component.
Level 3 visual hierarchy: 7 Fundamental Investment Pillars with subtle status indicators
and concise rationale.
"""

from typing import List, Dict, Any
import streamlit as st


def render_decision_pillars(pillars: List[Dict[str, Any]]):
    """Renders the 7-pillar executive decision matrix."""
    if not pillars:
        return

    color_styles = {
        "green": ("#34d399", "rgba(52, 211, 153, 0.12)", "#34d399"),
        "amber": ("#fbbf24", "rgba(251, 191, 36, 0.12)", "#fbbf24"),
        "red": ("#f87171", "rgba(248, 113, 113, 0.15)", "#f87171"),
        "blue": ("#38bdf8", "rgba(56, 189, 248, 0.12)", "#38bdf8")
    }

    cards_html = []
    for p in pillars:
        name = p.get("pillar_name", "Pillar")
        status = p.get("status", "MONITOR").replace("_", " ")
        col = p.get("color", "blue")
        fg, bg, border = color_styles.get(col, color_styles["blue"])
        rationale = p.get("summary_rationale", "")

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {border}; border-radius: 6px; padding: 0.85rem 1rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; gap: 8px;">
<span style="font-size: 0.82rem; font-weight: 600; color: #f8fafc; letter-spacing: 0.02em;">{name}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: {fg}; background: {bg}; border: 1px solid {fg}44; padding: 2px 7px; border-radius: 4px;">{status}</span>
</div>
<div style="font-size: 0.82rem; color: #94a3b8; line-height: 1.45;">{rationale}</div>
</div>""")

    html = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 0.75rem; margin-bottom: 1.5rem;">
{"".join(cards_html)}
</div>"""
    st.html(html)

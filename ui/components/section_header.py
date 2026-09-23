"""
Section Header Component.
Provides consistent, elegant headers for major workstation views with optional subtitle or badge.
"""

from typing import Optional
import streamlit as st


def render_section_header(title: str, subtitle: Optional[str] = None, badge: Optional[str] = None):
    """Renders a clean section title with consistent styling."""
    sub_html = f'<span style="font-size: 0.8rem; color: #64748b; font-weight: 400;">{subtitle}</span>' if subtitle else ""
    badge_html = f'<span style="font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); padding: 2px 7px; border-radius: 4px; font-weight: 600;">{badge}</span>' if badge else ""

    st.html(f"""<div style="display: flex; justify-content: space-between; align-items: baseline; margin-top: 1.5rem; margin-bottom: 0.75rem; border-bottom: 1px solid #1e293b; padding-bottom: 0.5rem; flex-wrap: wrap; gap: 8px;">
<div style="display: flex; align-items: baseline; gap: 10px;">
<h3 style="margin: 0; font-size: 1.15rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.01em;">{title}</h3>
{sub_html}
</div>
{badge_html}
</div>""")

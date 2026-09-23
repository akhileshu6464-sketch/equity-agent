"""
Error State Component.
Displays clean error alerts and boundary protection warnings.
"""

import streamlit as st


def render_error_state(title: str, message: str, is_critical: bool = False):
    """Renders a clean error alert."""
    border_col = "#f87171" if is_critical else "#fbbf24"
    bg_col = "rgba(248, 113, 113, 0.08)" if is_critical else "rgba(251, 191, 36, 0.08)"
    icon = "🚨" if is_critical else "⚠️"

    st.html(f"""<div style="background: {bg_col}; border: 1px solid {border_col}44; border-left: 4px solid {border_col}; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 1.5rem;">
<div style="font-size: 0.95rem; font-weight: 700; color: #f8fafc; margin-bottom: 0.35rem;">
{icon} {title}
</div>
<div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5;">
{message}
</div>
</div>""")

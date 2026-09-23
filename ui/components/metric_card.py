"""
Metric Card Component.
A lightweight, clean financial metric display without heavy borders or excessive code-block styling.
"""

from typing import Optional


def render_metric_card_html(
    label: str,
    value: str,
    sub_label: Optional[str] = None,
    delta_color: Optional[str] = None,
    accent: bool = False
) -> str:
    """Returns clean HTML for a single compact financial metric."""
    sub_html = ""
    if sub_label:
        color = delta_color if delta_color else "#94a3b8"
        sub_html = f'<div style="font-size: 0.72rem; color: {color}; margin-top: 2px; font-weight: 500;">{sub_label}</div>'

    val_color = "#38bdf8" if accent else "#f8fafc"

    return f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.65rem 0.85rem; display: flex; flex-direction: column; justify-content: space-between;">
<div style="font-size: 0.72rem; color: #94a3b8; font-weight: 500; text-transform: uppercase; letter-spacing: 0.03em; margin-bottom: 3px;">
{label}
</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: {val_color}; line-height: 1.2;">
{value}
</div>
{sub_html}
</div>"""

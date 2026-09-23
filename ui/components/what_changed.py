"""
What Changed Component.
Level 2 visual hierarchy: Concise multi-year trajectory cards with expandable Why, Evidence,
and Calculation details.
"""

from typing import Dict, Any, List
import streamlit as st


def render_what_changed(changes_data: Dict[str, Any]):
    """Renders the concise 'What Changed?' intelligence section with expandable details."""
    if not changes_data:
        st.info("No multi-year trajectory anomalies detected.")
        return

    summary = changes_data.get("summary_trajectory", "")
    alerts = changes_data.get("divergence_alerts", [])
    annual = changes_data.get("annual_changes", [])

    if summary:
        st.html(f"""<div style="background: rgba(56, 189, 248, 0.06); border: 1px solid rgba(56, 189, 248, 0.2); border-left: 3px solid #38bdf8; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1rem; font-size: 0.88rem; color: #cbd5e1; line-height: 1.5;">
<strong style="color: #38bdf8;">Trajectory Overview:</strong> {summary}
</div>""")

    # Divergence Alerts
    for a in alerts:
        sev = a.get("severity", "MEDIUM")
        border_col = "#ef4444" if sev == "CRITICAL" else ("#f97316" if sev == "HIGH" else "#fbbf24")
        bg_col = "rgba(239, 68, 68, 0.08)" if sev == "CRITICAL" else "rgba(249, 115, 22, 0.08)"
        title = a.get("title", "Trajectory Divergence")
        desc = a.get("description", "")
        ev = a.get("evidence", "")

        st.html(f"""<div style="background: {bg_col}; border: 1px solid {border_col}44; border-left: 3px solid {border_col}; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.65rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
<span style="font-weight: 600; font-size: 0.88rem; color: #f8fafc;">⚠️ {title}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: {border_col}; background: {border_col}22; padding: 1px 6px; border-radius: 3px;">[{sev}]</span>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 4px;">{desc}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">Evidence: {ev}</div>
</div>""")

    # Concise Key Metrics Delta Cards
    if annual:
        st.html("""<div style="font-size: 0.82rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; margin-top: 1rem; margin-bottom: 0.5rem;">
Core Line Item Trajectory Changes (Audited)
</div>""")

        for c in annual:
            metric = c.get("metric", "Metric")
            prev_p = c.get("previous_period", "Prior")
            curr_p = c.get("current_period", "Current")
            v_prev = c.get("previous_value", 0.0)
            v_curr = c.get("current_value", 0.0)
            pct = c.get("percentage_change")
            direction = c.get("direction", "STABLE")
            unit = c.get("unit", "")

            is_improving = direction in ["IMPROVING", "EXPANDING"]
            is_deteriorating = direction in ["DETERIORATING", "CONTRACTING"]
            dir_color = "#34d399" if is_improving else ("#f87171" if is_deteriorating else "#94a3b8")
            dir_symbol = "▲" if is_improving else ("▼" if is_deteriorating else "■")

            val_prev_str = f"{v_prev:,.1f}%" if unit == "PERCENT" else f"₹{v_prev:,.1f} Cr"
            val_curr_str = f"{v_curr:,.1f}%" if unit == "PERCENT" else f"₹{v_curr:,.1f} Cr"

            if unit == "PERCENT":
                bps = round((v_curr - v_prev) * 100.0, 0)
                chg_str = f"{bps:+.0f} bps"
            else:
                chg_str = f"{pct:+.1f}%" if pct is not None else f"{v_curr - v_prev:+,.1f}"

            expander_title = f"{metric}:  {val_prev_str} → {val_curr_str}  ({dir_symbol} {chg_str})"
            with st.expander(expander_title, expanded=False):
                col_calc, col_why = st.columns([1, 2])
                with col_calc:
                    st.html(f"""<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
<strong style="color: #94a3b8;">CALCULATION:</strong><br/>
• Prior Base ({prev_p}): <code>{val_prev_str}</code><br/>
• Audited ({curr_p}): <code>{val_curr_str}</code><br/>
• Variance: <strong style="color: {dir_color};">{dir_symbol} {chg_str}</strong><br/>
• Direction: <span style="color: {dir_color}; font-weight: 600;">{direction}</span>
</div>""")
                with col_why:
                    st.html(f"""<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.6;">
<strong style="color: #94a3b8;">WHY & OPERATIONAL DRIVER:</strong><br/>
Trajectory reflects operational variance between {prev_p} and {curr_p}. Grounded in primary financial statements filed with exchanges.
</div>""")

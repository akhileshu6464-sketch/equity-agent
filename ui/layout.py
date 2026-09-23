"""
Research Beast — Workstation Shell & Layout
Header, status banner, command search bar, and navigation chrome.
"""

from typing import Optional, Tuple, List
import streamlit as st


def render_workstation_top_bar():
    """Renders the top application header with brand and operational status."""
    st.html("""
    <div style="display: flex; justify-content: space-between; align-items: center; padding-bottom: 0.85rem; margin-bottom: 1.25rem; border-bottom: 1px solid #1e293b; flex-wrap: wrap; gap: 0.75rem;">
        <div style="display: flex; align-items: center; gap: 12px;">
            <div style="background: linear-gradient(135deg, #0284c7, #0369a1); color: #ffffff; font-weight: 800; font-size: 0.95rem; width: 32px; height: 32px; border-radius: 6px; display: flex; align-items: center; justify-content: center; letter-spacing: -0.02em;">
                RB
            </div>
            <div>
                <div style="font-weight: 700; font-size: 1.05rem; letter-spacing: -0.02em; color: #f8fafc; line-height: 1.1;">
                    RESEARCH BEAST
                </div>
                <div style="font-size: 0.72rem; color: #64748b; letter-spacing: 0.04em; text-transform: uppercase; font-weight: 500;">
                    Fundamental Investment Intelligence Workstation
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
            <div style="display: flex; align-items: center; gap: 6px; background: rgba(52, 211, 153, 0.08); border: 1px solid rgba(52, 211, 153, 0.25); padding: 4px 10px; border-radius: 9999px; font-size: 0.75rem; color: #34d399; font-weight: 600;">
                <span style="display: inline-block; width: 6px; height: 6px; border-radius: 50%; background: #34d399;"></span>
                <span>ZERO CONTAMINATION ENFORCED</span>
            </div>
            <div style="font-size: 0.74rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">
                15 AUDIT MODULES
            </div>
        </div>
    </div>
    """)


def render_command_bar(active_symbol: str = "") -> Optional[str]:
    """
    Renders the command search bar and benchmark quick-select pills.
    Returns the selected query if triggered, or None.
    """
    col_input, col_btn = st.columns([5, 1])

    with col_input:
        query_val = st.text_input(
            "Search Security or Company:",
            value=active_symbol,
            placeholder="Search company name, symbol or ticker (e.g. Vinati Organics, Ashoka Buildcon, Tata Motors)...",
            label_visibility="collapsed",
            key="workstation_search_input"
        )

    with col_btn:
        search_clicked = st.button("Audit Stock", type="primary", use_container_width=True, key="btn_audit_stock")

    # Quick Select Benchmark Row
    st.html("""
    <div style="font-size: 0.75rem; color: #64748b; margin-top: -0.3rem; margin-bottom: 0.35rem; display: flex; align-items: center; gap: 6px;">
        <span>Quick Benchmarks:</span>
    </div>
    """)

    quick_options = [
        ("VINATIORGA", "Chemicals"),
        ("ASHOKA", "Infra"),
        ("TATAMOTORS", "Auto"),
        ("HDFCBANK", "Banking"),
        ("RELIANCE", "Energy"),
        ("INFY", "IT"),
    ]

    cols = st.columns(len(quick_options))
    selected_from_chips = None

    for i, (sym, sector_label) in enumerate(quick_options):
        if cols[i].button(f"{sym} · {sector_label}", key=f"chip_{sym}", use_container_width=True):
            selected_from_chips = sym

    if selected_from_chips:
        return selected_from_chips
    if search_clicked and query_val.strip():
        return query_val.strip()

    return None

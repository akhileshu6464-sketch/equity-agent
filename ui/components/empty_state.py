"""
Empty State & Workstation Home Component.
Displayed when no company has been searched yet, providing architecture highlights,
benchmark quick-launches, and research capabilities.
"""

from typing import Optional
import streamlit as st


def render_workstation_home():
    """Renders the Workstation Home landing view."""
    st.html("""<div style="background: linear-gradient(180deg, #0d172a 0%, #080c14 100%); border: 1px solid #1e293b; border-radius: 8px; padding: 2rem 2.25rem; margin-top: 1rem; margin-bottom: 2rem;">
<div style="max-width: 820px;">
<div style="display: inline-block; font-size: 0.75rem; color: #38bdf8; background: rgba(56, 189, 248, 0.1); border: 1px solid rgba(56, 189, 248, 0.25); padding: 3px 10px; border-radius: 9999px; font-weight: 600; margin-bottom: 0.75rem;">
INSTITUTIONAL EQUITY INTELLIGENCE
</div>
<h2 style="font-size: 1.85rem; font-weight: 700; color: #f8fafc; letter-spacing: -0.025em; line-height: 1.25; margin-bottom: 0.75rem;">
Fundamental Investment Intelligence & Forensic Audit Workstation
</h2>
<p style="font-size: 0.95rem; color: #94a3b8; line-height: 1.6; margin-bottom: 1.5rem;">
Deterministic multi-year financial statement modeling, 15-module deep institutional equity research,
and real-time forensic accounting scans with 100% fail-closed company isolation.
</p>
</div>

<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-top: 1rem;">
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem;">
<div style="font-size: 0.85rem; font-weight: 700; color: #38bdf8; margin-bottom: 4px;">⚡ Zero Contamination</div>
<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">Fail-closed canonical boundaries ensure peer or cached data never leaks across companies.</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem;">
<div style="font-size: 0.85rem; font-weight: 700; color: #34d399; margin-bottom: 4px;">🛡️ Deterministic Math</div>
<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">All financial ratios, margins, and growth metrics are calculated in Python, with zero LLM hallucination.</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem;">
<div style="font-size: 0.85rem; font-weight: 700; color: #fbbf24; margin-bottom: 4px;">🔬 20+ Forensic Scans</div>
<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">Automated scans detect accrual discrepancies, cash-flow divergence, and promoter pledging.</div>
</div>
<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem;">
<div style="font-size: 0.85rem; font-weight: 700; color: #c084fc; margin-bottom: 4px;">📑 Primary Disclosures</div>
<div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.5;">Every operational finding is anchored to annual reports, quarterly filings, and concalls.</div>
</div>
</div>
</div>""")

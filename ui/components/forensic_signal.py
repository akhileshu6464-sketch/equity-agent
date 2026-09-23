"""
Forensic Signal Component.
Level 4 visual hierarchy: Non-accusatory anomaly investigation cards with structured expanders
for findings, implications, management explanations, and evidence citations.
"""

from typing import List, Dict, Any
import streamlit as st


def render_forensic_audit(forensic_tests: List[Dict[str, Any]]):
    """Renders the 20+ non-accusatory forensic scan results cleanly."""
    if not forensic_tests:
        st.info("No forensic red flags or accounting anomalies detected.")
        return

    # Categorize tests
    flagged = []
    clean = []

    for t in forensic_tests:
        status = t.get("status", "NORMAL")
        if status in ["INVESTIGATE", "RISK_SIGNAL", "ANOMALY", "REVIEW_REQUIRED", "RED_FLAG"]:
            flagged.append(t)
        else:
            clean.append(t)

    # Summary count banner
    st.html(f"""<div style="display: flex; gap: 1rem; align-items: center; background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.65rem 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
<span style="font-size: 0.82rem; color: #94a3b8;">Audited Scans: <strong style="color: #f8fafc;">{len(forensic_tests)}</strong></span>
<span style="font-size: 0.82rem; color: #94a3b8;">Clean Scans: <strong style="color: #34d399;">{len(clean)}</strong></span>
<span style="font-size: 0.82rem; color: #94a3b8;">Investigations Required: <strong style="color: {'#f87171' if flagged else '#34d399'};">{len(flagged)}</strong></span>
</div>""")

    # Render flagged anomalies prominently
    if flagged:
        st.html("""<div style="font-size: 0.84rem; font-weight: 600; color: #f87171; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.65rem;">
Forensic Investigation Signals ({len(flagged)})
</div>""")

        for t in flagged:
            title = t.get("test_name", "Forensic Scan")
            status = t.get("status", "INVESTIGATE").replace("_", " ")
            finding = t.get("finding", "Discrepancy noted in reported figures.")
            why = t.get("why_it_matters", "May indicate working capital stress or revenue recognition divergence.")
            mgt = t.get("management_commentary", "No specific mitigating explanation provided in primary disclosures.")
            ev = t.get("evidence", "Financial statement disclosures.")

            expander_label = f"⚠️ {title} — [{status}]"
            with st.expander(expander_label, expanded=True):
                st.html(f"""<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
<div style="margin-bottom: 0.5rem;">
<strong style="color: #f87171;">WHAT WE FOUND:</strong><br/>
{finding}
</div>
<div style="margin-bottom: 0.5rem;">
<strong style="color: #fbbf24;">WHY IT MATTERS:</strong><br/>
{why}
</div>
<div style="margin-bottom: 0.5rem;">
<strong style="color: #38bdf8;">MANAGEMENT EXPLANATION / MITIGATING CONTEXT:</strong><br/>
{mgt}
</div>
<div style="font-size: 0.78rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; border-top: 1px solid #1e293b; padding-top: 4px;">
<strong>EVIDENCE / FILING CITATION:</strong> {ev}
</div>
</div>""")

    # Collapsed clean scans
    if clean:
        with st.expander(f"✓ Verified Clean Baseline Scans ({len(clean)})", expanded=False):
            items_html = []
            for t in clean:
                name = t.get("test_name", "Scan")
                finding = t.get("finding", "Normal")
                items_html.append(f"""<tr style="border-bottom: 1px solid #1e293b; font-size: 0.82rem;">
<td style="padding: 6px 10px; color: #cbd5e1; font-weight: 500;">{name}</td>
<td style="padding: 6px 10px; color: #34d399; font-weight: 600; text-align: center;"><span style="background: rgba(52, 211, 153, 0.12); padding: 2px 6px; border-radius: 4px;">PASSED</span></td>
<td style="padding: 6px 10px; color: #94a3b8; font-size: 0.78rem;">{finding}</td>
</tr>""")

            st.html(f"""<div style="overflow-x: auto;">
<table style="width: 100%; border-collapse: collapse;">
<thead>
<tr style="border-bottom: 1px solid #334155; font-size: 0.74rem; color: #94a3b8; text-transform: uppercase;">
<th style="text-align: left; padding: 6px 10px;">Forensic Scan</th>
<th style="text-align: center; padding: 6px 10px;">Status</th>
<th style="text-align: left; padding: 6px 10px;">Finding</th>
</tr>
</thead>
<tbody>
{"".join(items_html)}
</tbody>
</table>
</div>""")

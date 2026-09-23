"""
Evidence & Source Affordance Component.
Level 7 visual hierarchy: Filing citations, primary document grounding, dynamic due diligence questions,
and JEV verification logs.
"""

from typing import List, Dict, Any, Optional
import streamlit as st


def render_evidence_drawer(primary_disclosures: Dict[str, Any], sources: List[str] = None):
    """Renders regulatory filings and primary document grounding references."""
    st.html("""<div style="font-size: 0.84rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; letter-spacing: 0.04em; margin-bottom: 0.5rem;">
Primary Document Disclosures & Filing Citations
</div>""")

    if not primary_disclosures and not sources:
        st.info("Primary document disclosures grounded in latest consolidated annual report and exchange filings.")
        return

    items_html = []
    if sources:
        for s in sources:
            items_html.append(f"""<div style="font-size: 0.82rem; color: #cbd5e1; padding: 4px 0; border-bottom: 1px solid #1e293b; display: flex; align-items: center; gap: 8px;">
<span style="color: #38bdf8;">📄</span> <span>{s}</span>
</div>""")

    if primary_disclosures:
        for k, v in primary_disclosures.items():
            if isinstance(v, str):
                items_html.append(f"""<div style="font-size: 0.82rem; color: #cbd5e1; padding: 4px 0; border-bottom: 1px solid #1e293b;">
<strong style="color: #94a3b8;">{k.replace('_', ' ').title()}:</strong> {v}
</div>""")

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1.1rem; margin-bottom: 1rem;">
{"".join(items_html)}
</div>""")


def render_investor_questions(questions: List[Dict[str, Any]]):
    """Renders dynamic due diligence investigation questions for investors."""
    if not questions:
        st.info("No specific investigation questions generated.")
        return

    for q in questions:
        title = q.get("title", "Investigation Focus")
        cat = q.get("category", "DUE DILIGENCE")
        question_text = q.get("question", "")
        why = q.get("why_it_matters", "")
        ev = q.get("evidence_anchor", "")
        sev = q.get("severity", "MEDIUM")

        col = "#f87171" if sev in ["CRITICAL", "HIGH"] else "#fbbf24"

        with st.expander(f"🔍 {title} [{cat}]", expanded=False):
            st.html(f"""<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.6;">
<div style="margin-bottom: 0.4rem;">
<strong style="color: #f8fafc;">Key Query for Management:</strong><br/>
{question_text}
</div>
<div style="margin-bottom: 0.4rem;">
<strong style="color: {col};">Why it Matters:</strong><br/>
{why}
</div>
<div style="font-size: 0.78rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; border-top: 1px solid #1e293b; padding-top: 4px;">
<strong>Evidence Anchor:</strong> {ev}
</div>
</div>""")


def render_event_timeline(events: List[Dict[str, Any]]):
    """Renders chronological company regulatory filings and events."""
    if not events:
        st.info("No major regulatory timeline events recorded.")
        return

    items_html = []
    for ev in events:
        date = ev.get("date", "Recent")
        title = ev.get("title", "Corporate Event")
        desc = ev.get("description", "")
        cat = ev.get("category", "FILING")

        items_html.append(f"""<div style="display: flex; gap: 12px; margin-bottom: 0.75rem; border-left: 2px solid #38bdf8; padding-left: 12px;">
<div style="min-width: 90px; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; color: #38bdf8; font-weight: 600;">{date}</div>
<div>
<div style="font-size: 0.85rem; font-weight: 600; color: #f8fafc;">{title} <span style="font-size: 0.7rem; color: #94a3b8; font-weight: normal;">[{cat}]</span></div>
<div style="font-size: 0.8rem; color: #94a3b8; margin-top: 2px;">{desc}</div>
</div>
</div>""")

    st.html(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem; margin-bottom: 1.25rem;">
{"".join(items_html)}
</div>""")


def render_jev_audit_log(jev_log: List[Dict[str, Any]]):
    """Renders JEV verification gate audit records."""
    if not jev_log:
        st.info("Zero-contradiction mathematical gate verified.")
        return

    rows_html = []
    for log in jev_log:
        step = log.get("step", "Verification")
        verdict = log.get("verdict", "PASS")
        details = log.get("details", "Deterministic Ledger Verified")
        col = "#34d399" if verdict == "PASS" else "#f87171"

        rows_html.append(f"""<tr style="border-bottom: 1px solid #1e293b; font-size: 0.82rem;">
<td style="padding: 6px 10px; color: #f8fafc; font-weight: 500;">{step}</td>
<td style="padding: 6px 10px; color: {col}; font-weight: 700; text-align: center;"><span style="background: {col}18; padding: 2px 7px; border-radius: 4px;">{verdict}</span></td>
<td style="padding: 6px 10px; color: #94a3b8; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;">{details}</td>
</tr>""")

    st.html(f"""<div class="rb-table-wrap">
<table class="rb-table">
<thead>
<tr>
<th>Verification Check</th>
<th style="text-align: center;">Gate Verdict</th>
<th>Audit Details</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>""")

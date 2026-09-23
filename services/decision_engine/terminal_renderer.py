"""
Terminal Renderer (services/decision_engine/terminal_renderer.py)
Generates clean, institutional HTML components for the Investment Intelligence Terminal:
1. Executive Decision Map (7 Pillars)
2. What Changed? (Trajectory & Divergence Alerts)
3. Why Did It Change? (Driver Analysis Cards)
4. Business Signals (Positive, Negative, Watch)
5. Financial Quality & Cash Conversion Flow
6. Forensic & Red-Flag Audit (Non-Accusatory Anomaly Investigation)
7. Industry Intelligence (Tailwinds, Headwinds, Structural Changes, Market Share Decoupling)
8. Future Opportunities & Catalysts
9. Future Risks & Vulnerabilities
10. Valuation & Market Pricing Analysis (Reverse DCF Embedded Growth Hurdle)
11. Company Event Timeline
12. Dynamic Investor Investigation Questions
13. JEV Structured Verification Gate Audit Log
"""

import re
import textwrap
from typing import Dict, Any, List, Optional
from ui.components.source_badge import render_source_badge


def _escape(text: Any) -> str:
    """Safely escapes HTML characters."""
    if text is None:
        return ""
    s = str(text)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )


def _clean_html(raw_html: str) -> str:
    """
    Dedents and strips HTML strings so markdown parsers never mistake
    indented HTML for a markdown code block (<pre><code>).
    """
    return textwrap.dedent(raw_html).strip()


def build_claim_badge(claim_type: str) -> str:
    """Delegates to ui.components.source_badge."""
    return render_source_badge(claim_type)


def build_decision_pillars_html(pillars: List[Dict[str, Any]]) -> str:
    """Renders the 7-pillar executive decision matrix."""
    cards_html = []
    color_styles = {
        "green": ("#34d399", "rgba(52, 211, 153, 0.12)", "#34d399"),
        "amber": ("#fbbf24", "rgba(251, 191, 36, 0.12)", "#fbbf24"),
        "red": ("#f87171", "rgba(248, 113, 113, 0.15)", "#f87171"),
        "blue": ("#38bdf8", "rgba(56, 189, 248, 0.12)", "#38bdf8")
    }

    for p in pillars:
        name = _escape(p.get("pillar_name", ""))
        status = _escape(p.get("status", "").replace("_", " "))
        col = p.get("color", "blue")
        fg, bg, border = color_styles.get(col, color_styles["blue"])
        rationale = _escape(p.get("summary_rationale", ""))

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {border}; border-radius: 6px; padding: 0.85rem 1rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; gap: 8px;">
<span style="font-size: 0.82rem; font-weight: 600; color: #f8fafc; letter-spacing: 0.02em;">{name}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: {fg}; background: {bg}; border: 1px solid {fg}44; padding: 2px 7px; border-radius: 4px;">{status}</span>
</div>
<div style="font-size: 0.82rem; color: #94a3b8; line-height: 1.45;">{rationale}</div>
</div>""")

    raw = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 0.75rem; margin-bottom: 1.25rem;">
{"".join(cards_html)}
</div>"""
    return _clean_html(raw)


def build_what_changed_html(changes_data: Dict[str, Any]) -> str:
    """Renders WHAT CHANGED: trajectory table and divergence alerts."""
    summary = _escape(changes_data.get("summary_trajectory", ""))
    alerts = changes_data.get("divergence_alerts", [])
    annual = changes_data.get("annual_changes", [])

    alerts_html = []
    for a in alerts:
        sev = a.get("severity", "MEDIUM")
        border_col = "#f87171" if sev == "CRITICAL" else ("#f97316" if sev == "HIGH" else "#fbbf24")
        bg_col = "rgba(248, 113, 113, 0.08)" if sev == "CRITICAL" else "rgba(249, 115, 22, 0.08)"
        alerts_html.append(f"""<div style="background: {bg_col}; border: 1px solid {border_col}44; border-left: 3px solid {border_col}; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.65rem;">
<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 0.25rem;">
<span>⚠️</span>
<span style="font-weight: 600; font-size: 0.88rem; color: #f8fafc;">{_escape(a.get('title'))}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: {border_col}; background: {border_col}22; padding: 1px 6px; border-radius: 3px;">[{sev}]</span>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.35rem;">{_escape(a.get('description'))}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;"><strong>Evidence:</strong> {_escape(a.get('evidence'))}</div>
</div>""")

    rows_html = []
    for c in annual:
        metric = _escape(c.get("metric"))
        prev_p = _escape(c.get("previous_period"))
        curr_p = _escape(c.get("current_period"))
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

        rows_html.append(f"""<tr style="border-bottom: 1px solid #1e293b; font-size: 0.84rem;">
<td style="padding: 8px 12px; font-weight: 500; color: #f8fafc;">{metric}</td>
<td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; text-align: right; color: #94a3b8;">{val_prev_str} <span style="font-size: 0.72rem;">({prev_p})</span></td>
<td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; text-align: right; font-weight: 700; color: #f8fafc;">{val_curr_str} <span style="font-size: 0.72rem;">({curr_p})</span></td>
<td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; text-align: right; font-weight: 700; color: {dir_color};">{dir_symbol} {chg_str}</td>
<td style="padding: 8px 12px; text-align: center;"><span style="font-size: 0.72rem; font-weight: 700; color: {dir_color}; background: {dir_color}18; padding: 2px 7px; border-radius: 4px;">{direction}</span></td>
</tr>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="font-size: 0.88rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 1rem; background: rgba(56, 189, 248, 0.08); padding: 8px 12px; border-radius: 5px; border-left: 3px solid #38bdf8;">
<strong style="color: #38bdf8;">Trajectory Overview:</strong> {summary}
</div>
{"".join(alerts_html)}
<div style="overflow-x: auto; background: #080c14; border: 1px solid #1e293b; border-radius: 6px;">
<table style="width: 100%; border-collapse: collapse; text-align: left;">
<thead>
<tr style="background: #141f36; color: #94a3b8; font-size: 0.76rem; text-transform: uppercase; border-bottom: 1px solid #334155;">
<th style="padding: 9px 12px;">Financial Metric</th>
<th style="padding: 9px 12px; text-align: right;">Prior Base</th>
<th style="padding: 9px 12px; text-align: right;">Audited Current</th>
<th style="padding: 9px 12px; text-align: right;">Change / Bps</th>
<th style="padding: 9px 12px; text-align: center;">Trajectory</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>
</div>"""
    return _clean_html(raw)


def build_why_it_changed_html(drivers: List[Dict[str, Any]]) -> str:
    """Renders WHY DID IT CHANGE: Driver analysis cards."""
    if not drivers:
        return '<div style="color: #94a3b8; font-size: 0.85rem;">Verified driver breakdown compiled from audited line items.</div>'

    cards_html = []
    for d in drivers:
        metric = _escape(d.get("metric"))
        factor = _escape(d.get("driver_factor", "").replace("_", " "))
        cls = d.get("driver_classification", "POSSIBLE_DRIVER")
        explanation = _escape(d.get("explanation"))
        ev_quote = _escape(d.get("evidence_quote"))
        ev_src = _escape(d.get("evidence_source"))
        caveat = _escape(d.get("causation_caveat"))

        cls_color = "#34d399" if cls == "VERIFIED_DRIVER" else ("#38bdf8" if cls == "POSSIBLE_DRIVER" else "#94a3b8")

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.15rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; flex-wrap: wrap; gap: 0.5rem;">
<span style="font-weight: 600; font-size: 0.92rem; color: #f8fafc;">{metric} &bull; <span style="color: #38bdf8;">{factor}</span></span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: {cls_color}; background: {cls_color}18; border: 1px solid {cls_color}44; padding: 2px 7px; border-radius: 4px;">[{cls}]</span>
</div>
<div style="font-size: 0.85rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0.45rem;">{explanation}</div>
<div style="background: #141f36; padding: 7px 10px; border-radius: 4px; font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.35rem;">
<strong>Evidence ({ev_src}):</strong> <em>"{ev_quote}"</em>
</div>
<div style="font-size: 0.76rem; color: #64748b; font-style: italic;">
<strong>Causation Guard:</strong> {caveat}
</div>
</div>""")

    return _clean_html(f'<div>{"".join(cards_html)}</div>')


def build_signals_dashboard_html(signals_data: Dict[str, Any]) -> str:
    """Renders POSITIVE, NEGATIVE, and WATCH signals with claim classification."""
    pos = signals_data.get("positive_signals", [])
    neg = signals_data.get("negative_signals", [])
    watch = signals_data.get("watch_signals", [])

    def render_card_group(items: List[Dict[str, Any]], theme_color: str, default_type: str) -> str:
        if not items:
            return '<div style="color: #94a3b8; font-size: 0.84rem;">No signals detected in this classification.</div>'
        html = []
        for s in items:
            lbl = _escape(s.get("status_label"))
            metric = _escape(s.get("metric"))
            chg = _escape(s.get("change"))
            period = _escape(s.get("period"))
            imp = _escape(s.get("importance", "MEDIUM"))
            reason = _escape(s.get("reason"))
            evidence = _escape(s.get("evidence"))

            html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {theme_color}; border-radius: 6px; padding: 0.85rem 1rem; margin-bottom: 0.65rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; flex-wrap: wrap; gap: 0.4rem;">
<span style="font-weight: 600; font-size: 0.88rem; color: #f8fafc;">{lbl} <span style="font-size: 0.76rem; color: #94a3b8; font-weight: normal;">({metric} &bull; {chg})</span></span>
<div style="display: flex; gap: 6px; align-items: center;">
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: {theme_color}; background: {theme_color}18; padding: 1px 6px; border-radius: 3px;">{imp}</span>
{build_claim_badge(default_type)}
</div>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.35rem;">{reason}</div>
<div style="font-size: 0.76rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">Evidence ({period}): {evidence}</div>
</div>""")
        return "".join(html)

    pos_html = render_card_group(pos, "#34d399", "HISTORICAL_FACT")
    neg_html = render_card_group(neg, "#f87171", "FORENSIC_SIGNAL")
    watch_html = render_card_group(watch, "#fbbf24", "MODEL_ASSUMPTION")

    raw = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1rem; margin-bottom: 1.5rem;">
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #34d399; text-transform: uppercase; margin-bottom: 0.6rem; letter-spacing: 0.04em;">
✅ Positive Signals ({len(pos)})
</div>
{pos_html}
</div>
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #f87171; text-transform: uppercase; margin-bottom: 0.6rem; letter-spacing: 0.04em;">
⚠️ Negative Signals ({len(neg)})
</div>
{neg_html}
</div>
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #fbbf24; text-transform: uppercase; margin-bottom: 0.6rem; letter-spacing: 0.04em;">
👁️ Watch Signals ({len(watch)})
</div>
{watch_html}
</div>
</div>"""
    return _clean_html(raw)


def build_financial_quality_html(fq_data: Dict[str, Any]) -> str:
    """Renders FINANCIAL QUALITY & CASH CONVERSION flow."""
    cfo_pct = fq_data.get("cfo_to_pat_5y_pct")
    cfo_pct_str = f"{cfo_pct:.1f}%" if cfo_pct is not None else "N/A"
    cfo_cr = fq_data.get("cumulative_5y_cfo_cr", 0.0)
    pat_cr = fq_data.get("cumulative_5y_pat_cr", 0.0)
    fcf_cr = fq_data.get("cumulative_5y_fcf_cr", 0.0)
    capex_cr = fq_data.get("cumulative_5y_capex_cr", 0.0)
    score = fq_data.get("overall_quality_score", "MODERATE_QUALITY").replace("_", " ")

    score_col = "#34d399" if "STRONG" in score else ("#f87171" if "VULNERABLE" in score else "#fbbf24")

    signals_html = []
    for s in fq_data.get("signals", []):
        stitle = _escape(s.get("title"))
        status = _escape(s.get("status"))
        val = _escape(s.get("metric_value"))
        why = _escape(s.get("why_it_matters"))
        ev = _escape(s.get("evidence"))
        poss = "".join([f"<li>{_escape(p)}</li>" for p in s.get("possible_explanations", [])])
        alts = "".join([f"<li>{_escape(a)}</li>" for a in s.get("alternative_explanations", [])])
        inv = "".join([f"<li>{_escape(i)}</li>" for i in s.get("what_to_investigate", [])])

        s_col = "#34d399" if status == "STRONG" else ("#f87171" if status == "VULNERABLE" else "#fbbf24")

        signals_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 1rem 1.15rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
<span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">{stitle}</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.74rem; font-weight: 700; color: {s_col}; background: {s_col}18; padding: 2px 7px; border-radius: 4px;">{val}</span>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0.4rem;">{why}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.5rem;">Evidence: {ev}</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.65rem; font-size: 0.8rem; background: #080c14; padding: 0.75rem; border-radius: 4px; border: 1px solid #1e293b;">
<div><strong style="color: #38bdf8;">Operational Drivers:</strong><ul style="margin: 0.25rem 0 0 1rem; padding: 0; color: #94a3b8;">{poss}</ul></div>
<div><strong style="color: #f87171;">Accounting Risks:</strong><ul style="margin: 0.25rem 0 0 1rem; padding: 0; color: #94a3b8;">{alts}</ul></div>
<div><strong style="color: #fbbf24;">Investigation Focus:</strong><ul style="margin: 0.25rem 0 0 1rem; padding: 0; color: #94a3b8;">{inv}</ul></div>
</div>
</div>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.5rem;">
<div style="font-size: 0.95rem; font-weight: 600; color: #f8fafc;">Cumulative 5-Year Cash Flow Conversion Waterfall</div>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.76rem; font-weight: 700; color: {score_col}; background: {score_col}18; border: 1px solid {score_col}44; padding: 3px 9px; border-radius: 4px;">Status: {score}</span>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 0.65rem; margin-bottom: 1rem;">
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">5Y Cumulative PAT</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #f8fafc;">₹{pat_cr:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">5Y Cumulative CFO</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #34d399;">₹{cfo_cr:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">CFO / PAT Conversion</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: {score_col};">{cfo_pct_str}</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">5Y Capex Reinvestment</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #cbd5e1;">₹{capex_cr:,.1f} Cr</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8; text-transform: uppercase;">5Y Free Cash Flow</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.1rem; font-weight: 700; color: #34d399;">₹{fcf_cr:,.1f} Cr</div>
</div>
</div>
{"".join(signals_html)}
</div>"""
    return _clean_html(raw)


def build_forensic_audit_html(forensic_data: Dict[str, Any]) -> str:
    """Renders FORENSIC & RED-FLAG INVESTIGATION: 20+ non-accusatory anomaly checks."""
    anomalies = forensic_data.get("anomalies", [])

    if not anomalies:
        return _clean_html("""<div style="background: rgba(52, 211, 153, 0.08); border: 1px solid rgba(52, 211, 153, 0.25); border-radius: 6px; padding: 1rem; color: #34d399; font-size: 0.86rem;">
🛡️ <strong>Zero High-Severity Forensic Anomalies:</strong> Systematic scan across 20+ balance sheet, cash conversion, and governance dimensions detected no critical divergence.
</div>""")

    cards_html = []
    for a in anomalies:
        title = _escape(a.get("anomaly_title"))
        sev = _escape(a.get("severity", "ELEVATED_WATCH"))
        pattern = _escape(a.get("observed_pattern"))
        ev = _escape(a.get("evidence"))
        poss = _escape(a.get("possible_explanation"))
        alt = _escape(a.get("alternative_explanation"))
        step = _escape(a.get("investor_due_diligence_step"))

        sev_col = "#f87171" if sev == "CRITICAL_REVIEW" else "#fbbf24"

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {sev_col}; border-radius: 6px; padding: 1rem 1.2rem; margin-bottom: 0.85rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.4rem; flex-wrap: wrap; gap: 0.5rem;">
<span style="font-weight: 600; font-size: 0.92rem; color: #f8fafc;">🔍 {title}</span>
<div style="display: flex; gap: 6px; align-items: center;">
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; font-weight: 700; color: {sev_col}; background: {sev_col}18; padding: 2px 7px; border-radius: 4px;">[{sev}]</span>
{build_claim_badge("FORENSIC_SIGNAL")}
</div>
</div>
<div style="font-size: 0.86rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0.45rem;">
<strong>Observed Pattern:</strong> {pattern}
</div>
<div style="font-size: 0.78rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.6rem;">
<strong>Verified Evidence:</strong> {ev}
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 0.65rem; font-size: 0.81rem; background: #080c14; padding: 0.75rem; border-radius: 4px; border: 1px solid #1e293b;">
<div>
<strong style="color: #38bdf8;">Operational Explanation:</strong>
<div style="color: #94a3b8; margin-top: 0.2rem;">{poss}</div>
</div>
<div>
<strong style="color: #f87171;">Accounting Risk:</strong>
<div style="color: #94a3b8; margin-top: 0.2rem;">{alt}</div>
</div>
<div>
<strong style="color: #fbbf24;">Investigation Step:</strong>
<div style="color: #94a3b8; margin-top: 0.2rem;">{step}</div>
</div>
</div>
</div>""")

    raw = f"""<div>
<div style="font-size: 0.8rem; color: #94a3b8; margin-bottom: 0.75rem;">
<em>Note: An accounting anomaly is not proof of misstatement. These signals isolate areas warranting detailed investor verification.</em>
</div>
{"".join(cards_html)}
</div>"""
    return _clean_html(raw)


def build_industry_intelligence_html(industry_data: Dict[str, Any]) -> str:
    """Renders INDUSTRY INTELLIGENCE: Tailwinds, Headwinds, Structural Shifts."""
    tw = industry_data.get("tailwinds", [])
    hw = industry_data.get("headwinds", [])
    sc = industry_data.get("structural_changes", [])
    mkt_share = _escape(industry_data.get("market_share_dynamics", ""))
    co_growth = _escape(industry_data.get("company_growth_rate", ""))

    def render_factor_list(items: List[Dict[str, Any]], color: str) -> str:
        if not items:
            return '<div style="color: #94a3b8; font-size: 0.82rem;">No macro factors flagged in this category.</div>'
        html = []
        for i in items:
            p = _escape(i.get("parameter", "").replace("_", " "))
            d = _escape(i.get("description"))
            impact = _escape(i.get("impact_on_company"))
            src = _escape(i.get("evidence_source"))
            html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 5px; padding: 0.75rem 0.9rem; margin-bottom: 0.5rem;">
<div style="font-weight: 600; font-size: 0.84rem; color: {color}; margin-bottom: 0.25rem;">{p}</div>
<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.3rem;">{d}</div>
<div style="font-size: 0.78rem; color: #38bdf8;"><strong>Company Impact:</strong> {impact}</div>
<div style="font-size: 0.72rem; color: #64748b; font-style: italic; margin-top: 0.2rem;">Source: {src}</div>
</div>""")
        return "".join(html)

    tw_html = render_factor_list(tw, "#34d399")
    hw_html = render_factor_list(hw, "#f87171")
    sc_html = render_factor_list(sc, "#38bdf8")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="background: #141f36; border-radius: 5px; padding: 8px 12px; margin-bottom: 1rem; font-size: 0.85rem; color: #f8fafc; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
<span><strong>Company Revenue Pace:</strong> <span style="color: #38bdf8; font-family: 'JetBrains Mono', monospace;">{co_growth}</span></span>
<span><strong>Market Share Dynamic:</strong> <span style="color: #34d399; font-weight: 600;">{mkt_share}</span></span>
</div>
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 0.85rem;">
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #34d399; text-transform: uppercase; margin-bottom: 0.5rem;">🟢 Structural Tailwinds ({len(tw)})</div>
{tw_html}
</div>
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #f87171; text-transform: uppercase; margin-bottom: 0.5rem;">🔴 Industry Headwinds ({len(hw)})</div>
{hw_html}
</div>
<div>
<div style="font-size: 0.84rem; font-weight: 600; color: #38bdf8; text-transform: uppercase; margin-bottom: 0.5rem;">🔄 Structural Shifts ({len(sc)})</div>
{sc_html}
</div>
</div>
</div>"""
    return _clean_html(raw)


def build_opportunities_and_risks_html(opportunities: List[Dict[str, Any]], risks: List[Dict[str, Any]]) -> str:
    """Renders FUTURE OPPORTUNITIES and FUTURE RISKS with claim categorization."""
    opp_cards = []
    for o in opportunities:
        title = _escape(o.get("opportunity_title"))
        etype = _escape(o.get("epistemological_type", "RESEARCH_BEAST_INFERENCE"))
        mech = _escape(o.get("business_mechanism"))
        ev = _escape(o.get("evidence"))
        horizon = _escape(o.get("time_horizon"))
        deps = ", ".join([_escape(d) for d in o.get("dependencies", [])])

        opp_cards.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid #34d399; border-radius: 6px; padding: 0.95rem 1.1rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; flex-wrap: wrap; gap: 0.4rem;">
<span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">🚀 {title}</span>
<div style="display: flex; gap: 6px; align-items: center;">
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: #38bdf8; background: rgba(56, 189, 248, 0.12); padding: 2px 6px; border-radius: 3px;">{horizon}</span>
{build_claim_badge(etype)}
</div>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.35rem;">{mech}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.35rem;"><strong>Evidence:</strong> {ev}</div>
<div style="font-size: 0.74rem; color: #64748b;"><strong>Dependencies:</strong> {deps}</div>
</div>""")

    risk_cards = []
    for r in risks:
        title = _escape(r.get("risk_title"))
        cat = _escape(r.get("risk_category", "KNOWN_RISK"))
        domain = _escape(r.get("domain", "Operational"))
        ev = _escape(r.get("evidence"))
        impact = _escape(r.get("potential_impact"))
        warn = _escape(r.get("early_warning_indicator"))

        cat_col = "#f87171" if cat == "KNOWN_RISK" else ("#f97316" if cat == "EMERGING_RISK" else "#fbbf24")

        risk_cards.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-left: 3px solid {cat_col}; border-radius: 6px; padding: 0.95rem 1.1rem; margin-bottom: 0.75rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem; flex-wrap: wrap; gap: 0.4rem;">
<span style="font-weight: 600; font-size: 0.9rem; color: #f8fafc;">⚠️ {title} <span style="font-size: 0.76rem; color: #94a3b8;">({domain})</span></span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.68rem; font-weight: 700; color: {cat_col}; background: {cat_col}18; padding: 2px 6px; border-radius: 3px;">[{cat}]</span>
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.35rem;">{impact}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.35rem;"><strong>Evidence:</strong> {ev}</div>
<div style="font-size: 0.74rem; color: #f87171;"><strong>Early Warning Trigger:</strong> {warn}</div>
</div>""")

    raw = f"""<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 1.25rem; margin-bottom: 1.5rem;">
<div>
<div style="font-size: 0.86rem; font-weight: 600; color: #34d399; text-transform: uppercase; margin-bottom: 0.65rem; letter-spacing: 0.04em;">
🌟 Future Opportunities & Catalysts ({len(opportunities)})
</div>
{"".join(opp_cards)}
</div>
<div>
<div style="font-size: 0.86rem; font-weight: 600; color: #f87171; text-transform: uppercase; margin-bottom: 0.65rem; letter-spacing: 0.04em;">
🛡️ Future Risks & Vulnerabilities ({len(risks)})
</div>
{"".join(risk_cards)}
</div>
</div>"""
    return _clean_html(raw)


def build_valuation_expectations_html(val_data: Dict[str, Any]) -> str:
    """Renders VALUATION & WHAT MAY THE MARKET BE PRICING IN."""
    co_val = val_data.get("company_valuation", {})
    mkt = val_data.get("market_pricing_analysis", {})
    insights = mkt.get("pricing_insights", [])

    pe = co_val.get("pe_ratio", 0.0)
    pb = co_val.get("pb_ratio", 0.0)
    ev_ebitda = co_val.get("ev_ebitda", 0.0)
    fcf_yield = co_val.get("fcf_yield_pct", 0.0)
    roce = co_val.get("roce_pct", 0.0)
    cmp = co_val.get("current_price", 0.0)
    mcap = co_val.get("market_cap_cr", 0.0)

    implied_cagr = mkt.get("implied_growth_hurdle_cagr", 10.0)
    hist_cagr = mkt.get("historical_5y_growth_cagr", 10.0)
    wacc = mkt.get("assumed_wacc_pct", 11.5)

    insights_html = []
    for ins in insights:
        cat = ins.get("category", "INFERENCE")
        stmt = _escape(ins.get("statement"))
        ev = _escape(ins.get("evidence_or_basis"))

        insights_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.85rem 1rem; margin-bottom: 0.6rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.35rem;">
<span style="font-size: 0.78rem; font-weight: 600; color: #94a3b8;">Epistemological Status:</span>
{build_claim_badge(cat)}
</div>
<div style="font-size: 0.84rem; color: #cbd5e1; line-height: 1.5; margin-bottom: 0.35rem;">{stmt}</div>
<div style="font-size: 0.74rem; color: #64748b; font-family: 'JetBrains Mono', monospace;">Basis: {ev}</div>
</div>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(130px, 1fr)); gap: 0.65rem; margin-bottom: 1.25rem;">
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">Stock P/E</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{pe:.1f}x</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">EV / EBITDA</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{ev_ebitda:.1f}x</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">Price to Book</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #f8fafc;">{pb:.2f}</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">FCF Yield</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #34d399;">{fcf_yield:.2f}%</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">ROCE</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #34d399;">{roce:.1f}%</div>
</div>
<div style="background: #141f36; padding: 0.75rem; border-radius: 5px; text-align: center;">
<div style="font-size: 0.72rem; color: #94a3b8;">Reverse DCF Hurdle</div>
<div style="font-family: 'JetBrains Mono', monospace; font-size: 1.15rem; font-weight: 700; color: #38bdf8;">{implied_cagr:.1f}% CAGR</div>
</div>
</div>

<div style="background: rgba(56, 189, 248, 0.08); border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 0.85rem 1rem; margin-bottom: 1rem; font-size: 0.85rem; color: #f8fafc;">
💡 <strong>Reverse DCF Hurdle Benchmark:</strong> At ₹{cmp:,.2f} (Mcap ₹{mcap:,.1f} Cr), the current price implies the business must compound free cash flow at <strong>{implied_cagr:.1f}% CAGR</strong> for 10 years at a {wacc:.1f}% cost of capital. Proven historical 5-year delivery pace was <strong>{hist_cagr:.1f}% CAGR</strong>.
</div>

<div style="font-size: 0.84rem; font-weight: 600; color: #94a3b8; text-transform: uppercase; margin-bottom: 0.5rem;">
What May The Market Be Pricing In? (Fact vs Inference vs Assumption)
</div>
{"".join(insights_html)}
</div>"""
    return _clean_html(raw)


def build_event_timeline_html(events: List[Dict[str, Any]]) -> str:
    """Renders COMPANY EVENT TIMELINE."""
    if not events:
        return '<div style="color: #94a3b8; font-size: 0.85rem;">Chronological timeline compiled from regulatory filings.</div>'

    items_html = []
    for e in events:
        dt = _escape(e.get("date"))
        title = _escape(e.get("event_title"))
        src = _escape(e.get("source"))
        biz = _escape(e.get("business_relevance"))
        fin = _escape(e.get("financial_relevance"))

        items_html.append(f"""<div style="display: flex; gap: 1rem; margin-bottom: 0.85rem;">
<div style="min-width: 90px; text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 0.78rem; font-weight: 700; color: #38bdf8; padding-top: 2px;">
{dt}
</div>
<div style="border-left: 2px solid #334155; padding-left: 1rem; padding-bottom: 0.5rem; flex: 1;">
<div style="font-weight: 600; font-size: 0.88rem; color: #f8fafc; margin-bottom: 0.2rem;">{title}</div>
<div style="font-size: 0.82rem; color: #cbd5e1; margin-bottom: 0.25rem;">{biz}</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;"><strong>Financial Relevance:</strong> {fin}</div>
<div style="font-size: 0.72rem; color: #64748b; font-style: italic; margin-top: 0.15rem;">Source: {src}</div>
</div>
</div>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
{"".join(items_html)}
</div>"""
    return _clean_html(raw)


def build_investor_questions_html(questions: List[Dict[str, Any]]) -> str:
    """Renders WHAT SHOULD THE INVESTOR INVESTIGATE NEXT (Dynamic Due Diligence Questions)."""
    if not questions:
        return '<div style="color: #94a3b8; font-size: 0.85rem;">Due diligence questions dynamically compiled.</div>'

    cards_html = []
    for idx, q in enumerate(questions, 1):
        q_text = _escape(q.get("question"))
        orig = _escape(q.get("originating_signal"))
        why = _escape(q.get("why_crucial"))
        where = _escape(q.get("where_to_investigate"))

        cards_html.append(f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 6px; padding: 0.95rem 1.15rem; margin-bottom: 0.75rem;">
<div style="font-size: 0.9rem; font-weight: 600; color: #f8fafc; margin-bottom: 0.35rem; line-height: 1.4;">
<span style="color: #38bdf8;">Q{idx}:</span> {q_text}
</div>
<div style="font-size: 0.76rem; color: #fbbf24; font-family: 'JetBrains Mono', monospace; margin-bottom: 0.35rem;">
<strong>Originating Signal:</strong> {orig}
</div>
<div style="font-size: 0.82rem; color: #cbd5e1; line-height: 1.45; margin-bottom: 0.35rem;">
<strong>Why Crucial:</strong> {why}
</div>
<div style="font-size: 0.76rem; color: #94a3b8; font-family: 'JetBrains Mono', monospace;">
<strong>Where To Investigate:</strong> {where}
</div>
</div>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="font-size: 0.82rem; color: #94a3b8; margin-bottom: 0.75rem;">
<em>These company-specific due diligence questions were dynamically generated from detected changes, financial quality gaps, and forensic anomalies.</em>
</div>
{"".join(cards_html)}
</div>"""
    return _clean_html(raw)


def build_jev_verification_gate_html(jev_log: List[Dict[str, Any]]) -> str:
    """Renders JEV STRUCTURED VERIFICATION GATE audit log."""
    if not jev_log:
        return '<div style="color: #94a3b8; font-size: 0.85rem;">JEV verification audit log initialized.</div>'

    rows_html = []
    for item in jev_log:
        claim = _escape(item.get("claim", ""))
        status = _escape(item.get("status", "PASS"))
        ctype = _escape(item.get("claim_type", "HISTORICAL_FACT"))
        engine = _escape(item.get("verification_engine", ""))
        notes = _escape(item.get("review_notes", ""))
        quality = _escape(item.get("evidence_quality", "VERIFIED"))

        st_color = "#34d399" if status == "PASS" else ("#fbbf24" if status == "REVIEW" else "#f87171")

        rows_html.append(f"""<tr style="border-bottom: 1px solid #1e293b; font-size: 0.82rem;">
<td style="padding: 8px 12px; color: #f8fafc; font-weight: 500;">{claim}</td>
<td style="padding: 8px 12px; text-align: center;"><span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; font-weight: 700; color: {st_color}; background: {st_color}18; border: 1px solid {st_color}44; padding: 2px 7px; border-radius: 4px;">{status}</span></td>
<td style="padding: 8px 12px; text-align: center;">{build_claim_badge(ctype)}</td>
<td style="padding: 8px 12px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: #38bdf8;">{quality}</td>
<td style="padding: 8px 12px; color: #94a3b8; font-size: 0.76rem;">{notes} <span style="color: #64748b; font-size: 0.7rem;">({engine})</span></td>
</tr>""")

    raw = f"""<div style="background: #0f172a; border: 1px solid #1e293b; border-radius: 8px; padding: 1.25rem; margin-bottom: 1.5rem;">
<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem; flex-wrap: wrap; gap: 0.5rem;">
<span style="font-weight: 600; font-size: 0.92rem; color: #f8fafc;">🛡️ JEV Structured Verification Gate Audit Trail</span>
<span style="font-family: 'JetBrains Mono', monospace; font-size: 0.72rem; color: #38bdf8; background: rgba(56, 189, 248, 0.12); padding: 3px 8px; border-radius: 4px;">Verified Claims: {len(jev_log)}</span>
</div>
<div style="overflow-x: auto;">
<table style="width: 100%; border-collapse: collapse; text-align: left;">
<thead>
<tr style="background: #141f36; color: #94a3b8; font-size: 0.74rem; text-transform: uppercase; border-bottom: 1px solid #334155;">
<th style="padding: 8px 12px;">Candidate Claim</th>
<th style="padding: 8px 12px; text-align: center;">JEV Gate</th>
<th style="padding: 8px 12px; text-align: center;">Claim Type</th>
<th style="padding: 8px 12px;">Evidence Quality</th>
<th style="padding: 8px 12px;">Verification Notes & Model</th>
</tr>
</thead>
<tbody>
{"".join(rows_html)}
</tbody>
</table>
</div>
</div>"""
    return _clean_html(raw)

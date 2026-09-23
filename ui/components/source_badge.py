"""
Epistemological Claim Badges.
Classifies statements as Fact, Management Guidance, Market Data, Forensic Signal, etc.
"""

from typing import Optional


def render_source_badge(claim_type: Optional[str]) -> str:
    """Returns an inline HTML badge for a claim type."""
    ctype = str(claim_type or "").upper()
    color_map = {
        "HISTORICAL_FACT": ("#38bdf8", "rgba(56, 189, 248, 0.12)", "FACT"),
        "MANAGEMENT_COMMENTARY": ("#c084fc", "rgba(192, 132, 252, 0.12)", "MANAGEMENT COMMENTARY"),
        "COMPANY_GUIDANCE": ("#22d3ee", "rgba(34, 211, 238, 0.12)", "GUIDANCE"),
        "MARKET_DATA": ("#94a3b8", "rgba(148, 163, 184, 0.12)", "MARKET DATA"),
        "INDUSTRY_FACT": ("#60a5fa", "rgba(96, 165, 250, 0.12)", "INDUSTRY FACT"),
        "ANALYST_ESTIMATE": ("#fbbf24", "rgba(251, 191, 36, 0.12)", "ANALYST ESTIMATE"),
        "MODEL_ASSUMPTION": ("#cbd5e1", "rgba(203, 213, 225, 0.12)", "MODEL ASSUMPTION"),
        "RESEARCH_BEAST_INFERENCE": ("#fb923c", "rgba(251, 146, 60, 0.12)", "INFERENCE"),
        "FORENSIC_SIGNAL": ("#f87171", "rgba(248, 113, 113, 0.15)", "FORENSIC SIGNAL"),
    }
    fg, bg, label = color_map.get(ctype, ("#94a3b8", "rgba(148, 163, 184, 0.12)", ctype or "DISCLOSURE"))
    return (
        f'<span style="font-family: \'JetBrains Mono\', monospace; font-size: 0.7rem; '
        f'font-weight: 600; color: {fg}; background: {bg}; border: 1px solid {fg}44; '
        f'padding: 2px 7px; border-radius: 4px; letter-spacing: 0.03em;">{label}</span>'
    )

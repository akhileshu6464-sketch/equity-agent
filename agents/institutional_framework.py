"""
Institutional Analysis Framework & Sector Protocols
Defines the institutional writing directive, sector-specific boundaries,
and specialized prompt builders for deep, uncompromised equity research.
"""

import json
from typing import Dict, Any

SYSTEM_INSTITUTIONAL_DIRECTIVE = """
You are an Executive Director of Institutional Equity Research producing an unabridged, buy-side initiation dossier.

MANDATORY WRITING & ANALYTICAL STANDARDS:
1. STRICT BAN ON SHALLOW SUMMARIES: Never write one-line summaries, vague bullet points, or generic filler. 
2. 4-TIER RIGOR FOR EVERY DIMENSION:
   - Level A (Data & Trajectory): Quantify multi-year performance with specific numbers, growth rates, or basis-point changes from the provided financial payload.
   - Level B (Operational Drivers): Unpack the exact business mechanics (pricing power, product mix shifts, cost inflation pass-through, branch vintage throughput, capacity utilization).
   - Level C (Peer Benchmarking): Compare the company directly against top domestic competitors.
   - Level D (Thesis Invalidation & Downside): Define the exact operational threshold where the investment case breaks.
3. ABSOLUTE SECTOR BOUNDARIES: Strictly follow the mandated and prohibited terminology for the stock's resolved archetype.
4. TONE: Candor, forensic skepticism, zero promotional language.
"""

SECTOR_INSTRUCTIONS = {
    "BFSI": """
    SECTOR PROTOCOL: BANKING / NBFC / FINANCIAL SERVICES
    - REQUIRED FOCUS: Net Interest Margins (NIM), Credit-to-Deposit (C/D) ratio, CASA mobilization, Gross/Net NPAs, Provision Coverage (PCR), Slippage ratios, Return on Assets (DuPont RoA tree), Tier-1 CET-1 capital headroom.
    - STRICT PROHIBITION: Never mention plant capex, inventory, raw materials, factories, working capital cycles, or supply chain bottlenecks.
    """,
    "MANUFACTURING": """
    SECTOR PROTOCOL: INDUSTRIAL / CONSUMER GOODS / MANUFACTURING
    - REQUIRED FOCUS: Gross Margin Return on Inventory (GMROI), Days Sales of Inventory (DSI), Cash Conversion Cycle (CCC), Plant Capacity Utilization, Gross vs EBITDA margin spreads, Maintenance vs Growth CapEx, Power/Fuel costs.
    - STRICT PROHIBITION: Never mention NIM, CASA, slippages, or credit costs.
    """,
    "TECH": """
    SECTOR PROTOCOL: IT SERVICES & SOFTWARE
    - REQUIRED FOCUS: Billable utilization, offshore-onsite delivery ratio, client concentration, voluntary attrition rates, TCV/ACV order pipeline, revenue per employee.
    - STRICT PROHIBITION: Never mention raw materials, factories, or inventory.
    """
}


def get_sector_protocol(is_bank: bool, sector: str = "", industry: str = "") -> str:
    """Returns the applicable sector instruction protocol."""
    if is_bank:
        return SECTOR_INSTRUCTIONS["BFSI"]
    combined = (sector + " " + industry).lower()
    if any(k in combined for k in ["tech", "software", "information technology", "it services"]):
        return SECTOR_INSTRUCTIONS["TECH"]
    return SECTOR_INSTRUCTIONS["MANUFACTURING"]


def build_moat_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional competitive moat and business model prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))
    
    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: AUDIT COMPETITIVE MOAT, PRICING POWER & BARRIERS TO ENTRY
Evaluate the company across the following 5 critical moat dimensions.
For EVERY dimension, you MUST provide a structured 4-tier institutional node:
{{
  "title": "Moat Dimension Name",
  "historical_trend_and_metrics": "Level A (Data & Trajectory): Multi-year figures, margin spreads, market share shifts (min 40-60 words).",
  "operational_mechanics_and_drivers": "Level B (Operational Drivers): Pricing power, switching costs, network effects, structural cost advantages (min 40-60 words).",
  "competitive_context_and_benchmarks": "Level C (Peer Benchmarking): Direct contrast against top 2-3 domestic listed competitors (min 40-60 words).",
  "thesis_implication_and_risks": "Level D (Thesis Invalidation): The precise structural or competitive threshold that breaks this moat (min 40-60 words)."
}}

DIMENSIONS TO EVALUATE:
1. {'Core Spread Defense & CASA Liability Franchise' if is_bank else 'Pricing Power & Gross Margin Durability'}
2. {'Underwriting Moat, Credit Algorithm & Risk Filtering' if is_bank else 'Intangible Assets, Brand Equity & Regulatory Moats'}
3. {'Customer Stickiness, Switching Costs & Cross-Sell Ratio' if is_bank else 'Switching Costs & Customer Retention Economics'}
4. {'Branch Network Vintage & Operational Cost Advantage' if is_bank else 'Structural Cost Leadership & Scale Economies'}
5. {'Network Effects & Ecosystem Dominance' if is_bank else 'Distribution Reach & Channel Moat'}

Output valid JSON with keys:
'summary', 'moat_rating' ('WIDE', 'NARROW', 'NONE'), 'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'dimension_1', 'dimension_2', 'dimension_3', 'dimension_4', 'dimension_5'.
"""


def build_forensic_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional forensic accounting and earnings quality prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: FORENSIC ACCOUNTING & EARNINGS INTEGRITY AUDIT
Audit the company across 4 forensic accounting domains using the 4-tier framework:
{{
  "title": "Forensic Dimension Name",
  "historical_trend_and_metrics": "Level A (Data & Trajectory): Quantify 5Y accruals, CFO/PAT, provisions, or capitalization rates (min 40-60 words).",
  "operational_mechanics_and_drivers": "Level B (Operational Drivers): Revenue recognition policies, working capital or provision mechanics (min 40-60 words).",
  "competitive_context_and_benchmarks": "Level C (Peer Benchmarking): Contrast against peer accounting conservatism (min 40-60 words).",
  "thesis_implication_and_risks": "Level D (Thesis Invalidation): Red flags, manipulation triggers, or aggressive accrual warnings (min 40-60 words)."
}}

DOMAINS TO EVALUATE:
1. {'Provisioning Adequacy & Slippage Forensics' if is_bank else 'Cash Flow Quality & CFO vs PAT Conversion'}
2. {'Asset Quality Classification & Restructuring Scrutiny' if is_bank else 'Revenue Quality & Aggressive Accrual Detection (Modified Jones Model)'}
3. {'Off-Balance Sheet Liabilities & Contingent Exposures' if is_bank else 'Depreciation Policy & Capitalization of Operating Expenses'}
4. {'Auditor Quality & Governance Checklist' if is_bank else 'Auditor Independence, Qualifications & Auditor Turnover'}

Output valid JSON with keys:
'summary', 'forensic_score' ('CLEAN', 'WATCHLIST', 'SEVERE_ALERT'), 'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'domain_1', 'domain_2', 'domain_3', 'domain_4', 'red_flags', 'forensic_checklist'.
"""


def build_leadership_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional leadership pedigree, crisis playbook and competitor benchmark prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: LEADERSHIP PEDIGREE, CRISIS PLAYBOOK & COMPETITOR BENCHMARK
Audit the management team, historical crisis execution, and listed competitors across 4 mandatory dimensions:

1. DIMENSION 1 (LEADERSHIP PEDIGREE & INCENTIVES):
   - Key executive track records (CEO/MD, CFO, Promoters), tenure, historical institutional pedigree.
   - Skin in the game: Promoter shareholding, pledge percentage, ESOP vesting.
   - Executive remuneration vs Standalone Net Profit ratio.
   - Board independence and second-line succession pipelines.

2. DIMENSION 2 (CRISIS PLAYBOOK & HISTORICAL DOWNTURN EXECUTION):
   - Empirical navigation through 2008 GFC, {'2018 IL&FS Liquidity Crisis' if is_bank else '2018 NBFC Liquidity Squeeze'}, 2020 COVID lockdowns, and raw material inflation cycles.
   - Counter-cyclical market share gains, balance sheet preservation, and avoidance of dilutive distressed equity issuances.

3. DIMENSION 3 (MANAGEMENT CREDIBILITY & COMMITMENT AUDIT):
   - 3-5 year historical guidance audit (revenue, margins, CapEx commissioning vs reported delivery).
   - Forensic integrity: Auditor resignations, corporate advances to promoter entities, arm's-length related-party transactions.
   - Formal Credibility Verdict: 'HIGH INTEGRITY', 'PRAGMATIC', or 'PROMOTER-EXTRACTIVE'.

4. DIMENSION 4 (DIRECT COMPETITOR BENCHMARK MATRIX):
   - Direct peer comparison against top 2-3 listed Indian competitors.
   - Comparison on scale, operating margins, RoE/RoIC, and market share migration.
   - Institutional rationale explaining valuation premium or discount.

Output valid JSON with keys:
'summary', 'credibility_verdict', 'risk_pill',
'dimension1_leadership_pedigree', 'dimension2_crisis_playbook',
'dimension3_credibility_audit', 'dimension4_competitor_matrix'.
"""


def build_valuation_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional valuation, reverse DCF/RoE and scenario analysis prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: VALUATION HURDLE, SCENARIOS & THESIS INVALIDATION
Construct an institutional valuation appraisal:

1. VALUATION HURDLE & REVERSE ENGINEERING:
   - {'Sustainable RoE Hurdle Rate vs Cost of Equity' if is_bank else 'Reverse DCF Implied 10Y FCF Growth Rate'}.
   - What operational performance is the current market price (CMP) pricing in?

2. 3-TIER SCENARIO MODEL (BEAR / BASE / BULL):
   - Bear Case: Downside assumptions, fair target price, expected drawdown.
   - Base Case: Realistic growth trajectory, fair value target, expected IRR.
   - Bull Case: Blue-sky operating leverage, multiple expansion target price.

3. THESIS INVALIDATION TRIGGERS:
   - Specific, quantifiable quarterly metrics that mandate an immediate thesis exit.

4. INSTITUTIONAL VERDICT:
   - Strong Buy, Buy / Accumulate, Hold / Fair Value, or Avoid / Trim.

Output valid JSON with keys:
'summary', 'primary_valuation', 'implied_hurdle_rate', 'institutional_rating', 'risk_pill',
'scenario_analysis': {{'bear_case': {{...}}, 'base_case': {{...}}, 'bull_case': {{...}}}},
'invalidation_triggers': [...].
"""

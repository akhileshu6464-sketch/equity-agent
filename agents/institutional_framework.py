"""
Institutional Analysis Framework & Sector Protocols
Defines the institutional writing directive, sector-specific boundaries,
and specialized prompt builders for deep, uncompromised equity research.
"""

import json
from typing import Dict, Any

ANALYST_SYSTEM_PROMPT = (
    "You are an institutional equity analyst with live web search access. "
    "Before drafting the audit, search for the target company's latest BSE/NSE exchange filings, "
    "recent concall transcripts, and real operating product lines. "
    "Ground all CapEx, peer comparisons, and guidance in verified public sources."
)

SYSTEM_INSTITUTIONAL_DIRECTIVE = f"""{ANALYST_SYSTEM_PROMPT}

You are an Executive Director of Institutional Equity Research producing an unabridged, buy-side initiation dossier.

MANDATORY WRITING & FORMATTING STANDARDS:
1. CONTINUOUS FLOWING PARAGRAPHS ONLY: All output must consist purely of coherent, multi-sentence continuous paragraphs (9–10 sentences each).
2. STRICT PROHIBITIONS:
   - Strictly NEVER generate markdown headers ('#', '##', '###', '####').
   - Strictly NEVER use standalone bold labels (e.g., 'Pillar 1:', 'Level A:', 'Trajectory & Metrics:', 'Domain 1:', 'Risk Verdict:').
   - Strictly NEVER generate bullet points ('*', '-', '•', '1.', '2.').
3. NATURAL PROSE WEAVING: You must weave all quantitative metrics (CAGR, margins, spreads, working capital days), operational drivers, competitive benchmarking against top listed peers, and downside thesis invalidation thresholds directly into natural, flowing prose transitions within each paragraph.
4. 4-TIER RIGOR FOR EVERY DIMENSION:
   - Level A (Data & Trajectory): Quantify multi-year performance with specific numbers, growth rates, or basis-point changes from the provided financial payload.
   - Level B (Operational Drivers): Unpack the exact business mechanics (pricing power, product mix shifts, cost inflation pass-through, branch vintage throughput, capacity utilization).
   - Level C (Peer Benchmarking): Compare the company directly against top domestic competitors.
   - Level D (Thesis Invalidation & Downside): Define the exact operational threshold where the investment case breaks.
   Ensure all four levels are woven seamlessly into one flowing 9-10 sentence narrative block.
5. ABSOLUTE SECTOR BOUNDARIES: Strictly follow the mandated and prohibited terminology for the stock's resolved archetype.
6. TONE: Candor, forensic skepticism, zero promotional language.
"""

SECTOR_INSTRUCTIONS = {
    "BFSI": """
    SECTOR PROTOCOL: BANKING / NBFC / FINANCIAL SERVICES
    - REQUIRED FOCUS: Net Interest Margins (NIM), Credit-to-Deposit (C/D) ratio, CASA mobilization, Gross/Net NPAs, Provision Coverage (PCR), Slippage ratios, Return on Assets (DuPont RoA tree), Tier-1 CET-1 capital headroom.
    - STRICT PROHIBITION: Never mention plant capex, inventory, raw materials, factories, working capital cycles, or supply chain bottlenecks.
    """,
    "CHEMICALS": """
    SECTOR PROTOCOL: SPECIALTY CHEMICALS / ADVANCED MATERIALS
    - REQUIRED FOCUS: Global market share in key proprietary chemistries (e.g. ATBS, IBB, Veeral Organics butyl phenols / antioxidants), formula-indexed feedstock pass-through contracts, continuous-flow synthesis block capacity utilization, customer qualification cycles (2-3 year innovator qualification moats), Zero Liquid Discharge (ZLD) environmental compliance, and ROCE/ROIC vs WACC spreads.
    - STRICT PROHIBITION: Strictly NEVER mention retail consumer dealer agreements, appliances, copper, steel, CASA, NIM, or banking deposits.
    """,
    "MANUFACTURING": """
    SECTOR PROTOCOL: INDUSTRIAL / CONSUMER GOODS / MANUFACTURING
    - REQUIRED FOCUS: Brand equity, Gross Margins, Raw Material Pass-through, Dealer/Distributor Touchpoints, Secondary Sales Velocity, Cash Conversion Cycle (CCC, DIO, DSO, DPO), Plant Capacity Utilization, ROCE, and ROIC vs WACC spreads.
    - STRICT PROHIBITION: Strictly NEVER mention 'CASA', 'NIM', 'net interest margin', 'deposits', 'loan book', 'branches', 'CET-1', 'CRAR', 'NPAs', 'slippages', 'PCR', or banking peers (e.g. HDFC Bank, ICICI Bank, Axis Bank, Kotak, SBI).
    """,
    "TECH": """
    SECTOR PROTOCOL: IT SERVICES & SOFTWARE
    - REQUIRED FOCUS: Billable utilization, offshore-onsite delivery ratio, client concentration, voluntary attrition rates, TCV/ACV order pipeline, revenue per employee.
    - STRICT PROHIBITION: Never mention raw materials, factories, inventory, CASA, NIM, or banking deposits.
    """
}


def get_sector_protocol(is_bank: bool, sector: str = "", industry: str = "") -> str:
    """Returns the applicable sector instruction protocol."""
    if is_bank:
        return SECTOR_INSTRUCTIONS["BFSI"]
    combined = (sector + " " + industry).lower()
    if any(k in combined for k in ["chemical", "fertilizer", "agrochemical", "polymer", "materials"]):
        return SECTOR_INSTRUCTIONS["CHEMICALS"]
    if any(k in combined for k in ["tech", "software", "information technology", "it services"]):
        return SECTOR_INSTRUCTIONS["TECH"]
    return SECTOR_INSTRUCTIONS["MANUFACTURING"]


def build_moat_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional competitive moat and business model prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))
    
    clean_sym = ticker.upper().replace(".NS", "").replace(".BO", "").strip()
    is_chem = (
        clean_sym in ["VINATIORGA", "DEEPAKNTR", "TATACHEM", "PIIND", "AARTIIND", "SRF", "NAVINFLUOR", "FLUOROCHEM", "ATUL", "CLEAN", "FINEORG", "ALKYLAMINE", "BALAMINES"]
        or any(k in (company_meta.get("sector", "") + " " + company_meta.get("industry", "")).lower() for k in ["chemical", "polymer", "materials"])
    ) and not is_bank

    if is_bank:
        p1_desc = "Pillar 1: Core Revenue Engine & NIM / Liability Defensibility (CASA ratio, cost of funds, retail deposit granularity)"
        p2_desc = "Pillar 2: Operating Efficiency & Branch / Digital Underwriting Throughput (Cost-to-Income, turnaround times)"
        p3_desc = "Pillar 3: Asset Quality & Credit Cost Trajectory (GNPA, NNPA, PCR, slippage ratio)"
        p4_desc = "Pillar 4: Regulatory Capital & Balance Sheet Strength (CET-1, CRAR, LCR, RBI stress-testing buffers)"
    elif is_chem:
        p1_desc = "Pillar 1: Proprietary Chemistry Moat, ATBS/IBB Global Market Share & Formula-Indexed Pass-Through (Raw material pass-through, export client stickiness)"
        p2_desc = "Pillar 2: Continuous-Flow Chemical Synthesis, Veeral Organics Integration & Regulatory Moat (Synthesis block utilization, innovator qualification barriers, environmental ZLD compliance)"
        p3_desc = "Pillar 3: Working Capital Dynamics & Export Supply Chain Governance (Debtor aging with global chemical innovators, inventory turnover, CFO/PAT conversion)"
        p4_desc = "Pillar 4: Capital Allocation & Balance Sheet Durability (ROCE, ROIC, zero-debt balance sheet, organic expansion into butyl phenols/antioxidants)"
    else:
        p1_desc = "Pillar 1: Brand Moat, Pricing Power & Margin Defensibility (Gross margins, pricing power against raw materials, product mix)"
        p2_desc = "Pillar 2: Distribution Network, Channel Throughput & Operating Leverage (Dealer/distributor touchpoints, secondary sales velocity, capacity utilization, operating EBITDA margins)"
        p3_desc = "Pillar 3: Working Capital Dynamics & Cash Conversion Cycle (DIO, DSO, DPO, inventory turnover, operating cash flow conversion)"
        p4_desc = "Pillar 4: Capital Allocation & Balance Sheet Durability (ROCE, ROIC, debt-to-equity, free cash flow generation, capex/M&A reinvestment)"

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: AUDIT COMPETITIVE MOAT, PRICING POWER & BARRIERS TO ENTRY
Evaluate the company across the 4 critical moat pillars below.
For EVERY pillar, provide a node with a unified continuous paragraph of 9 to 10 complete sentences in 'narrative_prose', as well as the granular fields:
{{
  "title": "Moat Pillar Name",
  "narrative_prose": "Exhaustive continuous flowing paragraph (9-10 sentences) weaving multi-year metrics, pricing power, competitive moats, peer benchmarks, and invalidation triggers without headers or bullets.",
  "historical_trend_and_metrics": "Multi-year figures, margin spreads, market share shifts.",
  "operational_mechanics_and_drivers": "Pricing power, switching costs, network effects, structural cost advantages.",
  "competitive_context_and_benchmarks": "Direct contrast against top 2-3 domestic listed competitors.",
  "thesis_implication_and_risks": "The precise structural or competitive threshold that breaks this moat."
}}

PILLARS TO EVALUATE:
1. {p1_desc}
2. {p2_desc}
3. {p3_desc}
4. {p4_desc}

Output valid JSON with keys:
'summary', 'moat_rating' ('WIDE', 'NARROW', 'NONE'), 'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'dimension_1', 'dimension_2', 'dimension_3', 'dimension_4',
'pillar_1', 'pillar_2', 'pillar_3', 'pillar_4'.
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
Audit the company across 4 forensic accounting domains.
For EVERY domain, provide a node with a unified continuous paragraph of 9 to 10 complete sentences in 'narrative_prose', as well as the granular fields:
{{
  "title": "Forensic Dimension Name",
  "narrative_prose": "Exhaustive continuous flowing paragraph (9-10 sentences) weaving accruals, cash flow quality, depreciation/capitalization, peer conservatism, and forensic warnings without headers or bullets.",
  "historical_trend_and_metrics": "5Y accruals, CFO/PAT, provisions, or capitalization rates.",
  "operational_mechanics_and_drivers": "Revenue recognition policies, working capital or provision mechanics.",
  "competitive_context_and_benchmarks": "Contrast against peer accounting conservatism.",
  "thesis_implication_and_risks": "Red flags, manipulation triggers, or aggressive accrual warnings."
}}

DOMAINS TO EVALUATE:
1. {'Provisioning Adequacy & Slippage Forensics' if is_bank else 'Cash Flow Quality & CFO vs PAT Conversion'}
2. {'Asset Quality Classification & Restructuring Scrutiny' if is_bank else 'Revenue Quality & Aggressive Accrual Detection (Modified Jones Model)'}
3. {'Capital Allocation Integrity & Auditor Track Record' if is_bank else 'Capital Allocation Integrity & Auditor Conservatism'}
4. Forensic Risk Verdict & Comprehensive Accounting Score

Output valid JSON with keys:
'summary', 'forensic_score' ('CLEAN', 'ELEVATED', 'HIGH_RISK'), 'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'domain_1', 'domain_2', 'domain_3', 'domain_4',
'red_flags', 'forensic_checklist'.
"""


def build_leadership_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool, peers: list) -> str:
    """Builds an institutional leadership pedigree, crisis playbook, and peer benchmark prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})
PRIMARY COMPETITORS: {', '.join(peers)}

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: LEADERSHIP PEDIGREE, CRISIS PLAYBOOK & COMPETITOR BENCHMARK AUDIT
Audit the company across the 4 governance and competitive dimensions below.
For EVERY dimension, provide a node with a unified continuous paragraph of 9 to 10 complete sentences in 'narrative_prose', as well as the granular fields:
{{
  "title": "Leadership Dimension Name",
  "narrative_prose": "Exhaustive continuous flowing paragraph (9-10 sentences) weaving executive credentials, skin-in-the-game, crisis navigation, guidance fulfillment, and peer benchmarks without headers or bullets.",
  "historical_trend_and_metrics": "Executive tenure, promoter pledge history, crisis survival metrics.",
  "operational_mechanics_and_drivers": "Governance checks, operational resilience, guidance tracking systems.",
  "competitive_context_and_benchmarks": "Direct contrast against listed peers ({', '.join(peers)}).",
  "thesis_implication_and_risks": "Governance breaches, guidance misses, or succession risks."
}}

DIMENSIONS TO EVALUATE:
1. Executive Leadership Profile & Promoter Skin-in-the-Game (key executives, tenure, remuneration alignment, zero promoter pledge)
2. Historical Crisis Playbook & Downturn Navigation (navigation through 2008 GFC, 2018 liquidity freeze, 2020 lockdowns, or feedstock inflation)
3. Promise vs Delivery Audit (3-year guidance tracking against audited delivery)
4. Head-to-Head Peer Comparison Matrix (direct benchmarking against {', '.join(peers)})

Output valid JSON with keys:
'summary', 'credibility_verdict' ('HIGH INTEGRITY', 'PRAGMATIC', 'PROMOTER-EXTRACTIVE'), 'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'dimension1_leadership_pedigree', 'dimension2_crisis_playbook', 'dimension3_credibility_audit', 'dimension4_competitor_matrix'.
"""


def build_valuation_prompt(ticker: str, financial_payload: Dict[str, Any], is_bank: bool) -> str:
    """Builds an institutional valuation hurdle rate and scenario analysis prompt."""
    company_meta = financial_payload.get("company_meta", {})
    company_name = company_meta.get("short_name", ticker)
    sector_protocol = get_sector_protocol(is_bank, company_meta.get("sector", ""), company_meta.get("industry", ""))

    return f"""
{SYSTEM_INSTITUTIONAL_DIRECTIVE}

{sector_protocol}

COMPANY TARGET: {company_name} ({ticker})

FINANCIAL PAYLOAD CONTEXT:
{json.dumps(financial_payload, indent=2)}

TASK: VALUATION HURDLE RATES, SCENARIOS & THESIS INVALIDATION AUDIT
Audit the company across valuation hurdles, 3 operational scenarios, and quantifiable invalidation triggers.
Provide a unified continuous flowing paragraph (9-10 sentences) in 'narrative_prose' weaving implied growth hurdle rates, scenario returns, and invalidation triggers without headers or bullets.

VALUATION DOMAINS TO EVALUATE:
1. Intrinsic Valuation Multiple Audit ({'P/ABV & DuPont RoA Tree' if is_bank else 'Reverse DCF & EV/EBITDA'})
2. 3-Scenario Return Framework (Bear, Base, and Bull operational trajectories and target prices)
3. Three Quantifiable Thesis Invalidation Triggers (Exact numerical thresholds)

Output valid JSON with keys:
'summary', 'narrative_prose', 'primary_valuation', 'implied_hurdle_rate',
'institutional_rating' ('BUY / ACCUMULATE', 'HOLD / FAIR VALUE', 'SELL / AVOID'),
'risk_pill' ('GREEN', 'YELLOW', 'RED'),
'scenario_analysis' (with 'bear_case', 'base_case', 'bull_case'),
'invalidation_triggers' (list of 3 strings).
"""

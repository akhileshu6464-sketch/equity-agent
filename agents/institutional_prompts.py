"""
Institutional Equity Research Master Prompt Templates
Eliminates shallow summaries and single-line bullet points.
Enforces 4-level analytical depth and strict sector boundaries.
"""

SYSTEM_INSTITUTIONAL_FRAMEWORK = """
You are an Executive Director of Institutional Equity Research preparing a buy-side initiation dossier.

MANDATORY RULES:
1. STRICT PROHIBITION: Never write one-line bullet points or generic summaries.
2. 4-LEVEL DEPTH FOR EVERY PARAMETER:
   - [Trajectory & Metrics]: Detail multi-year trends citing specific figures, percentages, or basis points.
   - [Operational Drivers]: Explain the exact mechanics (capacity utilization, branch vintage throughput, pricing realization, product mix).
   - [Peer Comparison]: Contrast performance directly against top 2 domestic listed peers.
   - [Thesis Invalidation]: State the exact numerical red flag that mandates cutting losses.
3. SECTOR DISCIPLINE:
   - For Banks/BFSI: Focus strictly on NIM, CASA ratio, Gross/Net NPAs, PCR, Cost of Funds, C/D ratio, and Tier-1 CET-1 capital. Never mention factories, raw material inflation, or inventory.
   - For Industrials/Consumer: Focus on GMROI, Cash Conversion Cycle, Plant Capacity, and Working Capital.
"""

def get_moat_prompt(ticker: str, company_name: str, sector: str, is_bank: bool, data_summary: str) -> str:
    if is_bank:
        sector_rules = "SECTOR: BFSI / LENDING. Focus strictly on CASA deposit durability, branch vintage productivity, net interest spreads, and Tier-1 capital absorption. Strictly prohibit mentions of factories, raw materials, or inventories."
        p3_desc = "3. Liability & Sourcing Risks (Granular CASA Retail Deposit Franchise & Interbank Wholesale Independence)"
        p4_desc = "4. Regulatory Capital Consumption (Tier-1 CET-1 Headroom & Risk-Weighted Asset Optimization)"
    else:
        sector_rules = "SECTOR: INDUSTRIAL / CONSUMER. Focus strictly on working capital velocity, pricing power pass-through, plant capacity utilization, and ROIC vs WACC spreads. Strictly prohibit mentions of CASA, NIM, or banking deposits."
        p3_desc = "3. Sourcing & Supply Chain Risks (Vendor Concentration, Component Sourcing & Working Capital Velocity)"
        p4_desc = "4. Capital Reinvestment & Capacity Expansion (ROIC vs WACC Spreads & Free Cash Flow Accretion)"
    
    return f"""
    COMPANY: {company_name} ({ticker})
    {sector_rules}
    
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 1: ECONOMIC MOAT & STRUCTURAL SCALABILITY.
    Provide an exhaustive, multi-paragraph analysis for each of these 4 pillars:
    1. Core Revenue Engine & Pricing Power Defensibility
    2. Operational Leverage & Branch/Unit Throughput Dynamics
    {p3_desc}
    {p4_desc}

    Format with bold section titles and deep, institutional paragraphs (minimum 120 words per pillar).
    """

def get_forensic_prompt(ticker: str, company_name: str, is_bank: bool, data_summary: str) -> str:
    p1_desc = "1. NII Realization, Provision Coverage Adequacy & Credit Cost Integrity" if is_bank else "1. Cash Flow vs Operating Profit Divergence (5-Year Cumulative CFO/PAT Conversion Quality)"
    return f"""
    COMPANY: {company_name} ({ticker})
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 2: FORENSIC AUDIT & EARNINGS QUALITY.
    Provide detailed multi-paragraph evaluations for:
    {p1_desc}
    2. Revenue Recognition, Asset Aging, and Contingent Liabilities
    3. Capital Allocation Integrity & Auditor Track Record
    4. Forensic Risk Verdict: Rate as LOW, MODERATE, or ELEVATED with evidence-backed justification.
    """

def get_leadership_prompt(ticker: str, company_name: str, is_bank: bool, peers: list) -> str:
    return f"""
    COMPANY: {company_name} ({ticker})
    PRIMARY COMPETITORS: {', '.join(peers)}

    Generate CHAPTER 3: LEADERSHIP PEDIGREE, CRISIS PLAYBOOK & COMPETITOR BENCHMARK.
    Provide detailed multi-paragraph evaluations for:
    1. Executive Leadership Profile & Promoter Skin-in-the-Game (tenure, capital allocation track record, alignment)
    2. Historical Crisis Playbook: Analyze specifically how this management team navigated past stress periods (2008 GFC, 2018 IL&FS, 2020 lockdowns, or severe inflation)
    3. Promise vs Delivery Audit: 3-year audit of management's forward guidance against actual reported results
    4. Head-to-Head Peer Comparison Matrix: Directly compare {ticker} against {', '.join(peers)} on return spreads ({'RoA/RoE' if is_bank else 'ROIC/ROCE'}), cost efficiency, and market share migration.
    """

def get_valuation_prompt(ticker: str, company_name: str, is_bank: bool, data_summary: str) -> str:
    triggers_desc = "Exact numerical thresholds (e.g. net slippages >1.50%, deposit margin compression, or CET-1 erosion <12.5%)" if is_bank else "Exact numerical thresholds (e.g. gross margin compression >250 bps, Cash Conversion Cycle blowing out beyond 68 days, or ROIC falling below WACC)"
    return f"""
    COMPANY: {company_name} ({ticker})
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 4: VALUATION HURDLE RATES & THESIS INVALIDATION.
    Provide detailed evaluations for:
    1. Intrinsic Valuation Multiple Audit ({ 'P/ABV & DuPont RoA Tree' if is_bank else 'Reverse DCF & EV/EBITDA' })
    2. 3-Scenario Return Matrix (Bear / Base / Bull) with explicit catalysts
    3. Three Quantifiable Thesis Invalidation Triggers: {triggers_desc} that break the investment case.
    """

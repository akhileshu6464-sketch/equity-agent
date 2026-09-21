"""
Institutional Equity Research Master Prompt Templates
Eliminates shallow summaries and single-line bullet points.
Enforces 4-level analytical depth, verified public sources grounding, and strict sector boundaries.
"""

ANALYST_SYSTEM_PROMPT = (
    "You are an institutional equity analyst with live web search access. "
    "Before drafting the audit, search for the target company's latest BSE/NSE exchange filings, "
    "recent concall transcripts, and real operating product lines. "
    "Ground all CapEx, peer comparisons, and guidance in verified public sources."
)

SYSTEM_INSTITUTIONAL_FRAMEWORK = f"""
{ANALYST_SYSTEM_PROMPT}

You are an Executive Director of Institutional Equity Research preparing an unabridged buy-side initiation dossier.

MANDATORY CONTEXT LOCKING & FACT-CHECKING RULES:
Analyze the target company STRICTLY using the context inside <verified_financials> and <primary_disclosures>.
1. Primary Source Citations: Every claim regarding CapEx timelines, capacity expansions, product lines, margin drivers, or operational headwinds must include a citation (e.g. [Source: Q4FY26 Concall Transcript, Page 3] or [Source: CARE Credit Rating Rationale] or [Source: Screener.in / BSE Official Profile]).
2. Explicit Non-Disclosure Rule: If a specific metric, CapEx timeline, or management guidance figure is not found in the provided sources, you MUST output 'Not Disclosed in Management Filings'. Strictly NEVER synthesize, interpolate, or fabricate forward estimates.
3. Absolute Prohibition on Synthetic Templates: Never generate synthetic dealer networks, unverified commodity exposures (e.g. copper, steel), or placeholder project names (e.g. Project Unnati).
4. Hard Numerical Constants: All financial metrics (CAGRs, P/E, P/BV, ROCE, ROIC, Working Capital Days, Net Debt, 5-Year CFO/PAT conversion) MUST match the exact constants in <verified_financials>. Never introduce contradictory figures.

MANDATORY WRITING & FORMATTING RULES:
1. CONTINUOUS FLOWING PARAGRAPHS ONLY: All output must consist purely of coherent, multi-sentence continuous paragraphs (9–10 sentences each).
2. STRICT PROHIBITIONS:
   - Strictly NEVER generate markdown headers ('#', '##', '###', '####').
   - Strictly NEVER use standalone bold labels (e.g., 'Pillar 1:', 'Level A:', 'Trajectory & Metrics:', 'Domain 1:', 'Risk Verdict:').
   - Strictly NEVER generate bullet points ('*', '-', '•', '1.', '2.').
3. NATURAL PROSE WEAVING: You must weave all quantitative metrics (CAGR, margins, spreads, working capital days), operational drivers, competitive benchmarking against top listed peers, and downside thesis invalidation thresholds directly into natural, flowing prose transitions within each paragraph.
4. SECTOR DISCIPLINE & ZERO CROSS-SECTOR CONTAMINATION:
   - For Banks/BFSI: Focus strictly on NIM, CASA ratio, Gross/Net NPAs, PCR, Cost of Funds, C/D ratio, and Tier-1 CET-1 capital. Strictly NEVER mention factories, plant capex, raw material inflation, or inventory.
   - For Specialty Chemicals / Advanced Materials: Focus strictly on verified product lines (e.g. ATBS, IBB, Veeral Organics butyl phenols / antioxidants), formula-indexed feedstock pass-through, customer qualification moats, and continuous-flow synthesis. Strictly NEVER mention retail dealer agreements, appliances, copper, or steel.
   - For IT Services: Focus strictly on deal TCV, book-to-bill, offshore/onsite mix, attrition, digital transformation contracts. Strictly NEVER mention dealer networks, factories, or inventory.
   - For Non-Financials: Focus strictly on Gross Margins, Raw Material Pass-through, Brand Equity, Distribution Reach, Cash Conversion Cycle (DIO/DSO/DPO), ROCE, and ROIC vs WACC. Strictly NEVER mention 'CASA', 'NIM', 'CET-1', 'CRAR', 'deposits', 'loan book', 'branches', 'slippages', 'PCR', or banking peers.
"""

def _format_context_blocks(verified_financials_block: str = "", primary_disclosures_block: str = "") -> str:
    blocks = []
    if verified_financials_block:
        blocks.append(verified_financials_block.strip())
    if primary_disclosures_block:
        blocks.append(primary_disclosures_block.strip())
    return ("\n\n" + "\n\n".join(blocks) + "\n\n") if blocks else ""


def get_moat_prompt(
    ticker: str,
    company_name: str,
    sector: str,
    is_bank: bool,
    data_summary: str,
    verified_financials_block: str = "",
    primary_disclosures_block: str = ""
) -> str:
    clean_sym = ticker.upper().replace(".NS", "").replace(".BO", "").strip()
    is_chemicals = clean_sym in ["VINATIORGA", "DEEPAKNTR", "TATACHEM", "PIIND", "AARTIIND", "SRF", "NAVINFLUOR", "FLUOROCHEM", "ATUL", "CLEAN", "FINEORG", "ALKYLAMINE", "BALAMINES"] or "chemical" in sector.lower() or "materials" in sector.lower()

    if is_bank:
        sector_rules = (
            "SECTOR: BFSI / LENDING.\n"
            "MANDATORY FOCUS: CASA deposit durability, branch vintage productivity, net interest spreads, asset quality (GNPA/NNPA/PCR), and Tier-1 CET-1 capital absorption.\n"
            "STRICT PROHIBITION: Strictly prohibit mentions of factories, raw materials, or inventories."
        )
        p1_focus = "Core Revenue Engine & NIM / Liability Defensibility (CASA ratio, cost of funds, retail deposit granularity)"
        p2_focus = "Operating Efficiency & Branch / Digital Underwriting Throughput (Cost-to-Income, turnaround times)"
        p3_focus = "Asset Quality & Credit Cost Trajectory (GNPA, NNPA, PCR, slippage ratio)"
        p4_focus = "Regulatory Capital & Balance Sheet Strength (CET-1, CRAR, LCR, RBI stress-testing buffers)"
    elif is_chemicals:
        sector_rules = (
            "SECTOR: SPECIALTY CHEMICALS / ADVANCED MATERIALS.\n"
            "MANDATORY FOCUS: Proprietary chemistry lines (e.g. ATBS, IBB, Veeral Organics butyl phenols / antioxidants), global market share, formula-indexed feedstock pass-through contracts, continuous-flow synthesis block capacity utilization, customer qualification cycles (2-3 year innovator qualification moats), and ROIC/ROCE vs WACC spreads.\n"
            "STRICT PROHIBITION: Strictly NEVER mention retail consumer dealer agreements, appliances, copper, steel, CASA, NIM, or banking deposits."
        )
        p1_focus = "Proprietary Chemistry Moat, ATBS/IBB Global Market Share & Formula-Indexed Pass-Through (Raw material pass-through, export stickiness)"
        p2_focus = "Continuous-Flow Chemical Synthesis, Veeral Organics Integration & Regulatory Moat (Synthesis block utilization, innovator qualification barriers, environmental ZLD compliance)"
        p3_focus = "Working Capital Dynamics & Export Supply Chain Governance (Debtor aging with global chemical innovators, inventory turnover, CFO/PAT conversion)"
        p4_focus = "Capital Allocation & Balance Sheet Durability (ROCE, ROIC, zero-debt balance sheet, organic expansion into butyl phenols/antioxidants)"
    else:
        sector_rules = (
            "SECTOR: INDUSTRIAL / CONSUMER / MANUFACTURING / FMCG.\n"
            "MANDATORY FOCUS: Brand equity, gross margins, pricing power against raw materials, dealer/distributor network velocity, working capital Cash Conversion Cycle (CCC, DIO, DSO, DPO), and ROIC/ROCE vs WACC spreads.\n"
            "STRICT PROHIBITION: Strictly NEVER mention 'CASA', 'NIM', 'net interest margin', 'deposits', 'loan book', 'branches', 'CET-1', 'CRAR', 'NPAs', 'slippages', 'PCR', or banking peers (e.g. HDFC Bank, ICICI Bank, Axis Bank, Kotak, SBI)."
        )
        p1_focus = "Brand Moat, Pricing Power & Margin Defensibility (Gross margins, pricing power against volatile raw materials, product mix)"
        p2_focus = "Distribution Network, Channel Throughput & Operating Leverage (Dealer/distributor touchpoints, secondary sales velocity, capacity utilization, operating EBITDA margins)"
        p3_focus = "Working Capital Dynamics & Cash Conversion Cycle (DIO, DSO, DPO, inventory turnover, operating cash flow conversion)"
        p4_focus = "Capital Allocation & Balance Sheet Durability (ROCE, ROIC, debt-to-equity, free cash flow generation, capex/M&A reinvestment)"
    
    ctx = _format_context_blocks(verified_financials_block, primary_disclosures_block)

    return f"""
    COMPANY: {company_name} ({ticker})
    {sector_rules}
    {ctx}
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 1: ECONOMIC MOAT & STRUCTURAL SCALABILITY.
    You must construct an exhaustive, continuous narrative for each of the 4 pillars below.
    For each pillar, write exactly one continuous, flowing paragraph of 9 to 10 complete sentences.
    Seamlessly weave the historical trajectory and verified numbers, the operational mechanics and drivers, the peer contrast against domestic competitors, and the explicit numerical thesis invalidation threshold into each paragraph.
    STRICT PROHIBITION: Do NOT use markdown headers, bold sub-labels, or bullet points. Output pure flowing paragraphs.

    Pillar 1 Focus: {p1_focus}
    Pillar 2 Focus: {p2_focus}
    Pillar 3 Focus: {p3_focus}
    Pillar 4 Focus: {p4_focus}
    """

def get_forensic_prompt(
    ticker: str,
    company_name: str,
    is_bank: bool,
    data_summary: str,
    verified_financials_block: str = "",
    primary_disclosures_block: str = ""
) -> str:
    p1_desc = "NII Realization, Provision Coverage Adequacy & Credit Cost Integrity" if is_bank else "Cash Flow vs Operating Profit Divergence (5-Year Cumulative CFO/PAT Conversion Quality)"
    ctx = _format_context_blocks(verified_financials_block, primary_disclosures_block)

    return f"""
    COMPANY: {company_name} ({ticker})
    {ctx}
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 2: FORENSIC AUDIT & EARNINGS QUALITY.
    Provide detailed narrative evaluations for each of the 4 forensic domains:
    1. {p1_desc}
    2. Revenue Recognition, Asset Aging, and Contingent Liabilities
    3. Capital Allocation Integrity & Auditor Track Record
    4. Forensic Risk Verdict and Overall Accounting Integrity
    
    For each domain, write exactly one continuous, flowing paragraph of 9 to 10 complete sentences.
    Weave forensic ratios, accounting mechanics, peer audit conservatism, and warning triggers directly into natural prose transitions.
    STRICT PROHIBITION: Do NOT use markdown headers, bold sub-labels, or bullet points. Output pure flowing paragraphs.
    """

def get_leadership_prompt(
    ticker: str,
    company_name: str,
    is_bank: bool,
    peers: list,
    verified_financials_block: str = "",
    primary_disclosures_block: str = ""
) -> str:
    ctx = _format_context_blocks(verified_financials_block, primary_disclosures_block)

    return f"""
    COMPANY: {company_name} ({ticker})
    PRIMARY COMPETITORS: {', '.join(peers)}
    {ctx}
    Generate CHAPTER 3: LEADERSHIP PEDIGREE, CRISIS PLAYBOOK & COMPETITOR BENCHMARK.
    Provide detailed narrative evaluations for each of the 4 leadership dimensions:
    1. Executive Leadership Profile & Promoter Skin-in-the-Game (tenure, capital allocation track record, alignment)
    2. Historical Crisis Playbook (navigation through 2008 GFC, 2018 liquidity freeze, 2020 lockdowns, or commodity inflation cycles)
    3. Promise vs Delivery Audit (3-year guidance tracking against reported delivery)
    4. Head-to-Head Peer Comparison Matrix (direct benchmark against {', '.join(peers)})
    
    For each dimension, write exactly one continuous, flowing paragraph of 9 to 10 complete sentences.
    Weave executive credentials, counter-cyclical crisis moves, guidance veracity, and competitor return spreads into natural prose transitions.
    STRICT PROHIBITION: Do NOT use markdown headers, bold sub-labels, or bullet points. Output pure flowing paragraphs.
    """

def get_valuation_prompt(
    ticker: str,
    company_name: str,
    is_bank: bool,
    data_summary: str,
    verified_financials_block: str = "",
    primary_disclosures_block: str = ""
) -> str:
    triggers_desc = "Exact numerical thresholds (e.g. net slippages >1.50%, deposit margin compression, or CET-1 erosion <12.5%)" if is_bank else "Exact numerical thresholds (e.g. gross margin compression >250 bps, Cash Conversion Cycle blowing out beyond 68 days, or ROIC falling below WACC)"
    ctx = _format_context_blocks(verified_financials_block, primary_disclosures_block)

    return f"""
    COMPANY: {company_name} ({ticker})
    {ctx}
    FINANCIAL BASELINE:
    {data_summary}

    Generate CHAPTER 4: VALUATION HURDLE RATES & THESIS INVALIDATION.
    Provide detailed narrative evaluations for:
    1. Intrinsic Valuation Multiple Audit ({ 'P/ABV & DuPont RoA Tree' if is_bank else 'Reverse DCF & EV/EBITDA' })
    2. 3-Scenario Return Framework (Bear, Base, and Bull operational trajectories and fair value outcomes)
    3. Three Quantifiable Thesis Invalidation Triggers: {triggers_desc}
    
    For each section, write a detailed, continuous, flowing paragraph of 9 to 10 complete sentences.
    Weave discount rates, implied growth hurdles, scenario assumptions, and exact invalidation metrics into natural prose transitions.
    STRICT PROHIBITION: Do NOT use markdown headers, bold sub-labels, or bullet points. Output pure flowing paragraphs.
    """

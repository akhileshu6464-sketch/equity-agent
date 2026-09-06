"""
Universal Sector Taxonomy & Routing Engine for NSE/BSE Equities
Defines the 12 canonical sector archetypes, required KPIs, primary valuation models, and banned metrics.
"""

from typing import Dict, Any, List, Optional

SECTOR_TAXONOMY = {
    "BFSI_BANKS": {
        "identifiers": ["Banks - Diversified", "Banks - Regional", "Private Sector Bank", "Public Sector Bank"],
        "display_name": "Banking & Financial Institutions",
        "required_kpis": [
            "NIM (Net Interest Margin)", "GNPA / NNPA Trend", "Provision Coverage Ratio (PCR)",
            "Credit Cost", "Slippages & Recoveries", "CASA Ratio %", "Credit-to-Deposit (C/D) Ratio",
            "Cost-to-Income Ratio", "CRAR & Tier-1 CET1 %", "DuPont RoA & RoE"
        ],
        "primary_valuation": "Price-to-Adjusted Book Value (P/ABV) & DuPont RoA Tree",
        "banned_metrics": ["EBITDA", "EV/EBITDA", "Free Cash Flow (FCF)", "Cash Conversion Cycle (CCC)", "Inventory Turnover", "DSO", "CapEx vs D&A", "Reverse DCF", "Graham Net-Net"]
    },
    "BFSI_NBFC": {
        "identifiers": ["Non-Banking Financial", "NBFC", "Housing Finance", "Microfinance", "Asset Management"],
        "display_name": "NBFCs, HFCs & Lending Institutions",
        "required_kpis": [
            "AUM Growth vs Disbursements", "Net Interest Spread (NIS)", "Borrowing Mix (CP vs NCD vs Bank Lines)",
            "ALM Bucket Matching (Liquidity Profile)", "Stage 2 & Stage 3 Assets %", "Collection Efficiency %",
            "Credit Cost on AUM", "Cost of Borrowings vs Yield on Loans", "Capital Adequacy (CRAR)"
        ],
        "primary_valuation": "P/BV relative to Sustainable RoE & AUM CAGR",
        "banned_metrics": ["EBITDA", "EV/EBITDA", "Free Cash Flow (FCF)", "CCC", "Inventory Turnover", "DSO", "DCF", "Graham Net-Net"]
    },
    "IT_SERVICES": {
        "identifiers": ["Information Technology Services", "IT Services & Consulting", "Software - Application"],
        "display_name": "IT Services & Enterprise Software",
        "required_kpis": [
            "TCV (Total Contract Value) & Net New Deal Wins", "LTM Voluntary Attrition Rate",
            "Employee Utilization Rate (ex-trainees)", "Offshore vs Onsite Delivery Mix",
            "Revenue per Billable Head", "Top 5 / Top 10 Client Concentration %", "Subcontracting Costs % of Sales"
        ],
        "primary_valuation": "FCF Yield, PEG Multiple & Earnings Power Value (EPV)",
        "banned_metrics": ["Inventory Turnover", "GMROI", "Plant Capacity Utilization", "Fixed Asset Turnover", "NIM", "Gross NPA"]
    },
    "CONSUMER_DURABLES_FMCG": {
        "identifiers": ["Consumer Durables", "Household Appliances", "Packaged Foods", "Personal Care", "FMCG"],
        "display_name": "Consumer Goods, Durables & FMCG",
        "required_kpis": [
            "Cash Conversion Cycle (CCC)", "Days Sales of Inventory (DSI)", "Gross Margin Return on Inventory (GMROI)",
            "Inventory Turnover Ratio", "Distribution Counter Reach & Active Outlets",
            "Raw Material Input Cost Inflation Lag (Pass-through Days)", "Volume vs Value Growth Spread"
        ],
        "primary_valuation": "Reverse DCF (FCF CAGR Hurdle) & Normalized Cash ROIC vs WACC",
        "banned_metrics": ["NIM", "PCR", "Gross NPA", "Loan Book", "TCV Deal Wins", "Order Book-to-Bill"]
    },
    "PHARMA_HEALTHCARE": {
        "identifiers": ["Drug Manufacturers", "Pharmaceuticals", "Healthcare Facilities", "Biotechnology", "CDMO"],
        "display_name": "Pharmaceuticals, Healthcare & CDMO",
        "required_kpis": [
            "US FDA 483 Inspection Observations & OAI/VAI Status", "R&D Expense as % of Revenue (>7% Benchmark)",
            "ANDA / DMF Filings Pipeline & Approvals", "CDMO/API Synthesis Capacity & Batch Yields",
            "Price Erosion in US Generics vs Domestic Branded Formulation Growth", "Cleanroom / Reactor Capacity (kL)"
        ],
        "primary_valuation": "Patent-Adjusted Mid-Cycle EV/EBITDA & Target P/E Multiple",
        "banned_metrics": ["NIM", "CASA Ratio", "Order Book-to-Bill", "SSSG", "App Installs"]
    },
    "INFRA_CAPITAL_GOODS_EPC": {
        "identifiers": ["Engineering - Industrial", "Heavy Electrical Equipment", "Infrastructure", "Construction"],
        "display_name": "Capital Goods, Infrastructure & EPC",
        "required_kpis": [
            "Order Book-to-Bill Ratio (>2.5x-3.0x)", "Net Working Capital as % of Order Book",
            "Retention Money & Unbilled Revenue Trajectory", "Execution Speed vs Milestone Billing",
            "Raw Material Price Escalation Clauses %", "Contingent Liabilities & Bank Guarantees Issued"
        ],
        "primary_valuation": "Mid-Cycle EV/EBITDA & Sum-of-the-Parts (SOTP)",
        "banned_metrics": ["Gross Margin Return on Inventory", "CASA Ratio", "TCV Contract Wins", "App GMV"]
    },
    "AUTOMOTIVE": {
        "identifiers": ["Auto Manufacturers", "Auto Parts", "Commercial Vehicles", "Two-Wheelers"],
        "display_name": "Automotive OEMs & Tier-1 Auto Components",
        "required_kpis": [
            "Volume Growth by Segment (EV / ICE / SUV / CV)", "Average Selling Price (ASP) Realization per Unit",
            "Plant Capacity Utilization % (Peak vs Normalized)", "OEM Content per Vehicle (Ancillaries)",
            "Raw Material Pass-through Mechanism (Steel/Aluminium/Lead)", "Export Revenue Mix %"
        ],
        "primary_valuation": "Mid-Cycle EV/EBITDA & RoCE Spread vs Cost of Capital",
        "banned_metrics": ["NIM", "Gross NPA", "Offshore Mix", "Client Concentration"]
    },
    "METALS_MINING": {
        "identifiers": ["Steel", "Aluminum", "Other Industrial Metals & Mining", "Coal"],
        "display_name": "Metals, Mining & Upstream Commodities",
        "required_kpis": [
            "EBITDA per Ton of Finished Metal", "Blended Realization Spread over Raw Materials",
            "Captive Iron Ore / Coking Coal / Bauxite Integration %", "Power Cost per Ton (Captive vs Grid)",
            "Blast Furnace / Smelter Capacity Utilization %", "Net Debt to EBITDA Cycle Sensitivity"
        ],
        "primary_valuation": "Mid-Cycle EV/EBITDA & Replacement Cost / EV per Ton of Capacity",
        "banned_metrics": ["Trailing P/E Ratio (Cyclical Value Trap)", "Terminal Multi-Stage DCF", "DSO"]
    },
    "OIL_GAS_ENERGY": {
        "identifiers": ["Oil & Gas Refining & Marketing", "Oil & Gas E&P", "Utilities - Regulated Electric", "Power Generation"],
        "display_name": "Oil, Gas, Refining & Power Generation",
        "required_kpis": [
            "Gross Refining Margin (GRM) vs Singapore Benchmark ($/bbl)", "Petrochemical Delta Spreads (Polymer/Polyester)",
            "Plant Load Factor (PLF) / Availability Factor (PAF) %", "Regulated Equity RoE Allowance",
            "Transmission Loss % / Distribution AT&C Losses", "Upstream Realization Net of Windfall Taxes"
        ],
        "primary_valuation": "Mid-Cycle EV/EBITDA, Regulated Equity Multiples & SOTP",
        "banned_metrics": ["Inventory GMROI", "CASA Ratio", "TCV Deal Wins"]
    },
    "REAL_ESTATE": {
        "identifiers": ["Real Estate - Development", "REIT", "Residential Real Estate"],
        "display_name": "Real Estate Developers & Operators",
        "required_kpis": [
            "Presales Booking Value & Area Sold (msft)", "Average Realization per Sq. Ft.",
            "Collections vs Construction Spend Velocity", "Total Realizable Land Bank Area & Cost Basis",
            "Embedded EBITDA Margin of Unrecognized Sales", "Net Debt to Operating Cash Flow"
        ],
        "primary_valuation": "Net Asset Value (NAV) per Share & P/NAV Discount/Premium",
        "banned_metrics": ["Trailing P/E Ratio (Distorted by Completion Accounting)", "Cash Conversion Cycle", "Inventory Turnover"]
    },
    "RETAIL_QUICK_SERVICE": {
        "identifiers": ["Specialty Retail", "Department Stores", "Restaurants", "Quick Service Restaurants (QSR)"],
        "display_name": "Retail Footprint & Consumer Services",
        "required_kpis": [
            "Same-Store Sales Growth (SSSG %)", "Store Addition Velocity & Net New Openings",
            "Average Revenue per Square Foot (Sales Density)", "Average Order Value (AOV) & Ticket Size",
            "Store-Level EBITDA Margin (Pre-Corporate Overhead)", "Payback Period per New Store"
        ],
        "primary_valuation": "EV/EBITDA, Reverse DCF & Pre-IndAS 116 Lease-Adjusted Returns",
        "banned_metrics": ["NIM", "Order Book-to-Bill", "US FDA Observations", "Raw Material Delta per Ton"]
    },
    "CHEMICALS_SPECIALTY": {
        "identifiers": ["Chemicals", "Specialty Chemicals", "Agrochemicals", "Fertilizers"],
        "display_name": "Specialty Chemicals & Materials",
        "required_kpis": [
            "Gross Margin Spread over Key Feedstock", "CapEx WIP (CWIP) as % of Gross Block",
            "Asset Turnover on Brownfield Expansions", "Share of Value-Added / Customized Formulations",
            "Export Mix vs Chinese Dumping Price Pressure", "Environmental Clearance & ETP Compliance"
        ],
        "primary_valuation": "EV/EBITDA & Normalized Cash ROIC vs 12% Hurdle",
        "banned_metrics": ["NIM", "CASA Ratio", "TCV Contract Wins"]
    }
}


def resolve_sector_archetype(yfinance_info: dict) -> dict:
    """Accurately maps any NSE/BSE stock into its proper institutional profile."""
    raw_sector = yfinance_info.get("sector", "")
    raw_industry = yfinance_info.get("industry", "")
    long_desc = yfinance_info.get("longBusinessSummary", "").lower()
    combined = f"{raw_sector} {raw_industry}".lower()

    for key, config in SECTOR_TAXONOMY.items():
        for identifier in config["identifiers"]:
            if identifier.lower() in combined:
                res = dict(config)
                res["sector_key"] = key
                return res

    # Match against long description if sector/industry was sparse
    for key, config in SECTOR_TAXONOMY.items():
        for identifier in config["identifiers"]:
            if identifier.lower() in long_desc:
                res = dict(config)
                res["sector_key"] = key
                return res

    # Fallback to standard consumer goods / durables if unmatched
    fallback = dict(SECTOR_TAXONOMY["CONSUMER_DURABLES_FMCG"])
    fallback["sector_key"] = "CONSUMER_DURABLES_FMCG"
    return fallback


def get_archetype_by_key(sector_key: str) -> dict:
    """Returns the archetype configuration for a given canonical sector key."""
    if sector_key in SECTOR_TAXONOMY:
        res = dict(SECTOR_TAXONOMY[sector_key])
        res["sector_key"] = sector_key
        return res
    fallback = dict(SECTOR_TAXONOMY["CONSUMER_DURABLES_FMCG"])
    fallback["sector_key"] = "CONSUMER_DURABLES_FMCG"
    return fallback


def is_metric_banned(archetype: dict, metric_name: str) -> bool:
    """Checks if a metric is prohibited for the given sector archetype."""
    if not archetype:
        return False
    banned = [b.lower() for b in archetype.get("banned_metrics", [])]
    m_lower = metric_name.lower()
    return any(b in m_lower or m_lower in b for b in banned)

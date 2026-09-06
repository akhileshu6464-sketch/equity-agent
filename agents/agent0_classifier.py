"""
Agent 0: Classifier
System prompt loaded from: agent0_classifier.txt
Assigns the company to exactly one of the 12 standard sectors and outputs the routing profile JSON.
Integrated with Universal Sector Taxonomy & Routing Engine (sector_guard.py).
"""

import re
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.sector_guard import resolve_sector_archetype, get_archetype_by_key, SECTOR_TAXONOMY


class Agent0Classifier(BaseAgent):
    """Institutional Equity Classification Specialist."""

    SECTORS = [config["display_name"] for config in SECTOR_TAXONOMY.values()]

    # Deterministic fallback dictionary for Nifty 50 giants and conglomerates
    CONGLOMERATE_OVERRIDES = {
        "RELIANCE.NS": ("OIL_GAS_ENERGY", "Oil, Gas, Energy & Utilities", "O2C (Refining & Petrochemicals), Telecom (Jio) & Retail"),
        "RELIANCE.BO": ("OIL_GAS_ENERGY", "Oil, Gas, Energy & Utilities", "O2C (Refining & Petrochemicals), Telecom (Jio) & Retail"),
        "LT.NS": ("INFRA_CAPITAL_GOODS_EPC", "Infrastructure, EPC & Logistics", "Heavy Engineering, Construction & Defense EPC"),
        "LT.BO": ("INFRA_CAPITAL_GOODS_EPC", "Infrastructure, EPC & Logistics", "Heavy Engineering, Construction & Defense EPC"),
        "ITC.NS": ("CONSUMER_DURABLES_FMCG", "Consumer Durables & FMCG", "Cigarettes, FMCG & Agri-Business"),
        "ITC.BO": ("CONSUMER_DURABLES_FMCG", "Consumer Durables & FMCG", "Cigarettes, FMCG & Agri-Business"),
        "TATAMOTORS.NS": ("AUTOMOTIVE", "Manufacturing, Industrial & Automotive", "Commercial Vehicles, Passenger Vehicles & EV Mobility"),
        "TATAMOTORS.BO": ("AUTOMOTIVE", "Manufacturing, Industrial & Automotive", "Commercial Vehicles, Passenger Vehicles & EV Mobility"),
        "TCS.NS": ("IT_SERVICES", "Technology & SaaS / IT Services", "Enterprise IT Consulting & Digital Engineering"),
        "TCS.BO": ("IT_SERVICES", "Technology & SaaS / IT Services", "Enterprise IT Consulting & Digital Engineering"),
        "HDFCBANK.NS": ("BFSI_BANKS", "Banking, NBFCs & Financial Services (BFSI)", "Retail & Corporate Lending, Deposits & Payments"),
        "HDFCBANK.BO": ("BFSI_BANKS", "Banking, NBFCs & Financial Services (BFSI)", "Retail & Corporate Lending, Deposits & Payments"),
        "CROMPTON.NS": ("CONSUMER_DURABLES_FMCG", "Consumer Durables & FMCG", "Electric Consumer Durables (Fans, Pumps, Lighting & Small Domestic Appliances)"),
        "CROMPTON.BO": ("CONSUMER_DURABLES_FMCG", "Consumer Durables & FMCG", "Electric Consumer Durables (Fans, Pumps, Lighting & Small Domestic Appliances)")
    }

    def __init__(self):
        super().__init__(
            name="Agent 0: Classifier",
            role="Assigns company to one of 12 standard sectors, identifies hybrid verticals, and outputs routing profile.",
            prompt_file="agent0_classifier.txt"
        )

    def analyze(self, company_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        ticker = company_data.get("symbol", "")
        short_name = company_data.get("short_name", ticker)
        
        # 1. Inject Ground Truth Metadata directly from yfinance
        raw_info = company_data.get("raw_info") or {}
        sector_yf = raw_info.get("sector") or company_data.get("sector") or ""
        industry_yf = raw_info.get("industry") or company_data.get("industry") or ""
        summary_yf = raw_info.get("longBusinessSummary") or company_data.get("summary") or ""

        # Augment system prompt with official ground truth metadata so agent never classifies blind
        ground_truth_context = (
            f"\n\n=== OFFICIAL GROUND TRUTH METADATA (yfinance) ===\n"
            f"• Ticker Symbol: {ticker}\n"
            f"• Company Legal Name: {short_name}\n"
            f"• Official yfinance Sector: {sector_yf}\n"
            f"• Official yfinance Industry: {industry_yf}\n"
            f"• Official yfinance Business Summary:\n{summary_yf}\n"
            f"=================================================\n"
        )
        prompt_with_truth = f"{self.system_prompt}{ground_truth_context}"

        # 2. Check Deterministic Overrides for Nifty 50 Giants and Conglomerates
        norm_key = ticker.strip().upper()
        if not norm_key.endswith(".NS") and not norm_key.endswith(".BO"):
            norm_key += ".NS"

        if norm_key in self.CONGLOMERATE_OVERRIDES:
            sector_key, primary_sector, sub_vertical = self.CONGLOMERATE_OVERRIDES[norm_key]
            archetype = get_archetype_by_key(sector_key)
            if "RELIANCE" in norm_key:
                hybrid_verticals = [
                    "Telecommunications & Digital Services (Jio Infocomm)",
                    "Organized Retail & E-Commerce (Reliance Retail)",
                    "Green Energy Gigafactories (Solar, Hydrogen, Energy Storage)"
                ]
            elif "LT" in norm_key:
                hybrid_verticals = [
                    "Defense Shipbuilding & Heavy Weapon Systems",
                    "IT Services & Digital Engineering (LTIMindtree)",
                    "Power & Metallurgical Turnkey EPC"
                ]
            elif "ITC" in norm_key:
                hybrid_verticals = [
                    "Branded Packaged Foods & Personal Care FMCG",
                    "Paperboards, Paper & Specialty Packaging",
                    "Agri-Business & Hotels Franchise"
                ]
            elif "TATAMOTORS" in norm_key:
                hybrid_verticals = [
                    "Luxury Performance Vehicles (Jaguar Land Rover)",
                    "Electric Vehicles (EV) & Battery Ecosystem",
                    "Commercial Fleet Telematics & Financing"
                ]
            else:
                _, hybrid_verticals = self._identify_sub_verticals(ticker, short_name, primary_sector, industry_yf, summary_yf)
        else:
            # Universal Sector Archetype Resolution via sector_guard
            archetype = resolve_sector_archetype({
                "sector": sector_yf,
                "industry": industry_yf,
                "longBusinessSummary": summary_yf
            })
            sector_key = archetype["sector_key"]
            primary_sector = archetype["display_name"]
            sub_vertical, hybrid_verticals = self._identify_sub_verticals(ticker, short_name, primary_sector, industry_yf, summary_yf)

        # 3. Revenue Engine Summary (>60% revenue and operating profit generator)
        revenue_engine = self._generate_revenue_engine_summary(ticker, short_name, primary_sector, sub_vertical, summary_yf)

        routing_profile = {
            "ticker": ticker,
            "sector_key": sector_key,
            "primary_sector": primary_sector,
            "display_name": archetype.get("display_name", primary_sector),
            "sub_vertical": sub_vertical,
            "revenue_engine_summary": revenue_engine,
            "required_kpis": archetype.get("required_kpis", []),
            "primary_valuation": archetype.get("primary_valuation", ""),
            "banned_metrics": archetype.get("banned_metrics", []),
            "archetype": archetype
        }

        flags = [
            f"**Assigned Sector (1 of 12)**: {primary_sector} (`{sector_key}`)",
            f"**Sub-Vertical**: {sub_vertical}",
            f"**Primary Valuation**: {archetype.get('primary_valuation', 'N/A')}",
            f"**Secondary / Hybrid Verticals**: {', '.join(hybrid_verticals) if hybrid_verticals else 'None identified'}",
            f"**Revenue Engine**: {revenue_engine}"
        ]

        return {
            "agent_name": self.name,
            "role": self.role,
            "system_prompt": prompt_with_truth,
            "risk_pill": "GREEN",
            "routing_profile": routing_profile,
            "sector_key": sector_key,
            "primary_sector": primary_sector,
            "display_name": archetype.get("display_name", primary_sector),
            "sub_vertical": sub_vertical,
            "hybrid_verticals": hybrid_verticals,
            "revenue_engine_summary": revenue_engine,
            "required_kpis": archetype.get("required_kpis", []),
            "primary_valuation": archetype.get("primary_valuation", ""),
            "banned_metrics": archetype.get("banned_metrics", []),
            "archetype": archetype,
            "summary": f"Classified under **{archetype.get('display_name', primary_sector)}** (`{sector_key}`) with sub-vertical **{sub_vertical}**. {revenue_engine}",
            "flags": flags,
            "audit_metrics": {
                "Primary Sector": primary_sector,
                "Sector Key": sector_key,
                "Sub-Vertical": sub_vertical,
                "Primary Valuation": archetype.get("primary_valuation", "N/A"),
                "Required KPIs Count": len(archetype.get("required_kpis", [])),
                "Banned Metrics Count": len(archetype.get("banned_metrics", [])),
                "YFinance Sector": sector_yf or "N/A",
                "YFinance Industry": industry_yf or "N/A"
            }
        }

    def _identify_sub_verticals(self, ticker: str, name: str, primary_sector: str, industry: str, summary: str) -> tuple[str, List[str]]:
        s = f"{ticker} {name} {summary}".lower()
        sub_vertical = industry if industry else "Core Operations"
        hybrids = []

        if "crompton" in s:
            sub_vertical = "Electric Consumer Durables (Fans, Pumps, Lighting & Small Domestic Appliances)"
            hybrids = [
                "Kitchen Appliances & Cookware",
                "Solar Water Pumps & Agricultural Solar EPC",
                "Smart Home Connected Lighting / IoT Lighting Solutions"
            ]
        elif "reliance" in s:
            sub_vertical = "O2C (Refining & Petrochemicals), Telecom (Jio) & Retail"
            hybrids = [
                "Telecommunications & Digital Broadband (Jio Infocomm)",
                "Organized Retail & E-Commerce (Reliance Retail)",
                "Green Energy Gigafactories & Solar / Hydrogen Value Chain"
            ]
        elif "consumer" in primary_sector.lower():
            sub_vertical = "Consumer Electricals & Kitchen Appliances"
            hybrids = ["Commercial & Industrial Lighting Solutions", "Renewable Solar Installations"]
        elif "banking" in primary_sector.lower() or "nbfc" in primary_sector.lower():
            sub_vertical = "Retail & Corporate Lending"
            hybrids = ["Wealth Management & Mutual Fund Distribution", "General & Life Insurance Cross-Selling"]
        elif "technology" in primary_sector.lower() or "it" in primary_sector.lower():
            sub_vertical = "Enterprise IT Consulting & Digital Engineering"
            hybrids = ["Proprietary Cloud Platforms & IP Assets", "AI/ML Solutions & Workflow Automation"]
        elif "oil" in primary_sector.lower() or "energy" in primary_sector.lower():
            sub_vertical = "Hydrocarbon Refining, Petrochemicals & Energy Distribution"
            hybrids = ["Petrochemical Downstream Derivatives", "Renewable Energy & Biofuels"]
        elif "pharma" in primary_sector.lower():
            sub_vertical = "Active Pharmaceutical Ingredients (API) & Formulations"
            hybrids = ["Contract Development and Manufacturing (CDMO)", "Specialty Biosimilars"]
        elif "auto" in primary_sector.lower():
            sub_vertical = "Automotive OEM Mobility Solutions"
            hybrids = ["Electric Vehicle Powertrains", "Connected Vehicle Telematics"]
        elif "metals" in primary_sector.lower():
            sub_vertical = "Primary Metal Smelting & Rolling"
            hybrids = ["Captive Power Generation", "Value-Added Alloy Products"]
        elif "real estate" in primary_sector.lower():
            sub_vertical = "Residential & Commercial Property Development"
            hybrids = ["Ancillary Facility Management", "Leased Commercial Portfolios"]
        elif "infra" in primary_sector.lower():
            sub_vertical = "Industrial EPC & Civil Infrastructure"
            hybrids = ["Transportation & Rail EPC", "Renewable Energy Turnkey Systems"]
        elif "chemicals" in primary_sector.lower():
            sub_vertical = "Specialty Fine Chemicals & Polymers"
            hybrids = ["Agro-Intermediates", "Performance Industrial Materials"]

        return sub_vertical, hybrids

    def _generate_revenue_engine_summary(self, ticker: str, name: str, primary_sector: str, sub_vertical: str, summary: str) -> str:
        s = f"{ticker} {name}".lower()
        t = ticker.upper().strip()
        if "reliance" in s or t.startswith("RELIANCE"):
            return ("Reliance Industries operates primarily across Oil to Chemicals (O2C refining & petrochemicals), "
                    "Digital Services (Jio telecom & broadband), and organized Retail, with the O2C energy engine generating foundational operating cash flows.")
        if "crompton" in s or t.startswith("CROMPTON"):
            return ("Crompton Greaves Consumer Electricals generates over 65% of its revenues and operating profit from Electric Consumer Durables "
                    "(fans, pumps, and domestic appliances), with the remainder driven by lighting and kitchenware.")
        if "larsen" in s or "l&t" in s or t.startswith("LT."):
            return ("Larsen & Toubro operates primarily in Heavy Engineering, Infrastructure, and Defense EPC, "
                    "executing complex multi-billion dollar turnkey capital projects across India and international markets.")
        if "itc" in s or t.startswith("ITC."):
            return ("ITC Limited generates over 70% of its operating profit from Cigarettes and FMCG, "
                    "with complementary cash flows from Agri-Business, Paperboards, and Hotels.")
        if "tatamotors" in s or "tata motors" in s or t.startswith("TATAMOTORS"):
            return ("Tata Motors operates primarily across Commercial Vehicles, Passenger Vehicles, Electric Mobility, and luxury automotive through Jaguar Land Rover (JLR).")
        if "tcs" in s or "tata consultancy" in s or t.startswith("TCS."):
            return ("Tata Consultancy Services generates over 75% of its revenue from Enterprise IT Consulting, Application Development, and Digital Transformation Services.")
        if "hdfc" in s or t.startswith("HDFCBANK"):
            return ("HDFC Bank generates the majority of its operating profit from Net Interest Income across Retail, Commercial, and Corporate Banking advances alongside transactional fee income.")
        return f"{name} operates primarily as a provider of {sub_vertical} within the {primary_sector} sector, generating the majority of its cash flows from core market demand and commercial delivery contracts."

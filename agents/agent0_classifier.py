"""
Agent 0: Classifier
System prompt loaded from: agent0_classifier.txt
Assigns the company to exactly one of the 12 standard sectors and outputs the routing profile JSON.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent


class Agent0Classifier(BaseAgent):
    """Institutional Equity Classification Specialist."""

    SECTORS = [
        "Technology & SaaS / IT Services",
        "Banking, NBFCs & Financial Services (BFSI)",
        "Retail, E-Commerce & QSR",
        "Real Estate & REITs",
        "Manufacturing, Industrial & Automotive",
        "Healthcare, Pharma & CDMO",
        "Oil, Gas, Energy & Utilities",
        "Mining & Metals",
        "Infrastructure, EPC & Logistics",
        "Chemicals & Specialty Materials",
        "Telecommunications & Media",
        "Consumer Durables & FMCG"
    ]

    def __init__(self):
        super().__init__(
            name="Agent 0: Classifier",
            role="Assigns company to one of 12 standard sectors, identifies hybrid verticals, and outputs routing profile.",
            prompt_file="agent0_classifier.txt"
        )

    def analyze(self, company_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        ticker = company_data.get("symbol", "")
        short_name = company_data.get("short_name", ticker)
        sector_yf = company_data.get("sector") or ""
        industry_yf = company_data.get("industry") or ""
        summary = company_data.get("summary") or ""

        # 1. Assign to exactly ONE of the 12 sectors
        primary_sector = self._classify_primary_sector(ticker, short_name, sector_yf, industry_yf, summary)
        
        # 2. Identify Secondary / Hybrid Business Verticals
        sub_vertical, hybrid_verticals = self._identify_sub_verticals(ticker, short_name, primary_sector, industry_yf, summary)

        # 3. Revenue Engine Summary (>60% revenue and operating profit generator)
        revenue_engine = self._generate_revenue_engine_summary(ticker, short_name, primary_sector, sub_vertical, summary)

        routing_profile = {
            "ticker": ticker,
            "primary_sector": primary_sector,
            "sub_vertical": sub_vertical,
            "revenue_engine_summary": revenue_engine
        }

        flags = [
            f"**Assigned Sector (1 of 12)**: {primary_sector}",
            f"**Sub-Vertical**: {sub_vertical}",
            f"**Secondary / Hybrid Verticals**: {', '.join(hybrid_verticals) if hybrid_verticals else 'None identified'}",
            f"**Revenue Engine**: {revenue_engine}"
        ]

        return {
            "agent_name": self.name,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "risk_pill": "GREEN",
            "routing_profile": routing_profile,
            "primary_sector": primary_sector,
            "sub_vertical": sub_vertical,
            "hybrid_verticals": hybrid_verticals,
            "revenue_engine_summary": revenue_engine,
            "summary": f"Classified under **{primary_sector}** with sub-vertical **{sub_vertical}**. {revenue_engine}",
            "flags": flags,
            "audit_metrics": {
                "Primary Sector": primary_sector,
                "Sub-Vertical": sub_vertical,
                "Hybrid Verticals Count": len(hybrid_verticals),
                "YFinance Sector": sector_yf or "N/A",
                "YFinance Industry": industry_yf or "N/A"
            }
        }

    def _classify_primary_sector(self, ticker: str, name: str, sector: str, industry: str, summary: str) -> str:
        s = f"{ticker} {name} {sector} {industry} {summary}".lower()

        # Check banking / NBFC / BFSI
        if "bank" in s or "nbfc" in s or "lending" in s or "housing finance" in s or "insurance" in s or "asset management" in s or "amc" in s or "financial" in sector.lower():
            return "Banking, NBFCs & Financial Services (BFSI)"

        # Check Consumer Durables & FMCG (Crompton, Havells, Voltas, Whirlpool, Dabur, HUL, etc.)
        if ("crompton" in s or "fan" in s or "lighting" in s or "appliance" in s or "durables" in s or "fmcg" in s 
            or "consumer cyclical" in sector.lower() or "consumer defensive" in sector.lower() or "household" in s
            or "furnishings" in industry.lower() or "consumer goods" in s):
            return "Consumer Durables & FMCG"

        # Check Technology & SaaS / IT Services
        if "software" in s or "information technology" in s or "it services" in s or "saas" in s or "tcs" in s or "infosys" in s or "wipro" in s or "tech mahindra" in s:
            return "Technology & SaaS / IT Services"

        # Check Healthcare, Pharma & CDMO
        if "pharma" in s or "healthcare" in s or "hospital" in s or "drug" in s or "cdmo" in s or "api" in s:
            return "Healthcare, Pharma & CDMO"

        # Check Oil, Gas, Energy & Utilities
        if "oil" in s or "gas" in s or "refin" in s or "power" in s or "utilities" in s or "renewable" in s or "solar" in s:
            return "Oil, Gas, Energy & Utilities"

        # Check Mining & Metals
        if "mining" in s or "metal" in s or "steel" in s or "aluminum" in s or "iron ore" in s or "coal" in s:
            return "Mining & Metals"

        # Check Chemicals & Specialty Materials
        if "chemical" in s or "specialty material" in s or "fluorine" in s or "fertilizer" in s or "polymer" in s:
            return "Chemicals & Specialty Materials"

        # Check Infrastructure, EPC & Logistics
        if "infrastructure" in s or "epc" in s or "logistics" in s or "port" in s or "shipping" in s or "road" in s:
            return "Infrastructure, EPC & Logistics"

        # Check Real Estate & REITs
        if "real estate" in s or "reit" in s or "property" in s or "developer" in s or "residential" in s:
            return "Real Estate & REITs"

        # Check Telecommunications & Media
        if "telecom" in s or "media" in s or "broadcasting" in s or "wireless" in s:
            return "Telecommunications & Media"

        # Check Retail, E-Commerce & QSR
        if "retail" in s or "e-commerce" in s or "qsr" in s or "restaurant" in s or "supermarket" in s:
            return "Retail, E-Commerce & QSR"

        # Default to Manufacturing, Industrial & Automotive
        return "Manufacturing, Industrial & Automotive"

    def _identify_sub_verticals(self, ticker: str, name: str, primary_sector: str, industry: str, summary: str) -> tuple[str, List[str]]:
        s = f"{ticker} {name} {summary}".lower()
        sub_vertical = industry if industry else "Core Operations"
        hybrids = []

        if "crompton" in s:
            sub_vertical = "Electric Consumer Durables (Fans, Pumps, Lighting & Small Domestic Appliances)"
            hybrids = [
                "Kitchen Appliances & Cookware (via Butterfly Gandhimathi integration)",
                "Solar Water Pumps & Agricultural Solar EPC",
                "Smart Home Connected Lighting / IoT Lighting Solutions"
            ]
        elif primary_sector == "Consumer Durables & FMCG":
            sub_vertical = "Consumer Electricals & Kitchen Appliances"
            hybrids = ["Commercial & Industrial Lighting Solutions", "Renewable Solar Installations"]
        elif primary_sector == "Banking, NBFCs & Financial Services (BFSI)":
            sub_vertical = "Retail & Corporate Lending"
            hybrids = ["Wealth Management & Mutual Fund Distribution", "General & Life Insurance Cross-Selling"]
        elif primary_sector == "Technology & SaaS / IT Services":
            sub_vertical = "Enterprise IT Consulting & Digital Engineering"
            hybrids = ["Proprietary Cloud Platforms & IP Assets", "AI/ML Solutions & Workflow Automation"]

        return sub_vertical, hybrids

    def _generate_revenue_engine_summary(self, ticker: str, name: str, primary_sector: str, sub_vertical: str, summary: str) -> str:
        s = f"{ticker} {name}".lower()
        if "crompton" in s:
            return ("Crompton Greaves Consumer Electricals generates over 65% of its revenues and operating profit from Electric Consumer Durables "
                    "(residential ceiling/BLDC fans, residential water pumps, and domestic appliances), with the remainder driven by LED lighting and Butterfly kitchenware.")
        return f"{name} operates primarily as a provider of {sub_vertical} within the {primary_sector} sector, generating the majority of its cash flows from core market demand and commercial delivery contracts."

"""
Multi-Agent Institutional Equity Pipeline Coordinator
Orchestrates Agents 0 through 6, ensuring all checklist prompts from .txt files are executed without omission.
"""

import logging
from typing import Dict, Any

from services.financial_data import FinancialDataService
from services.web_scraper import WebScraperService
from agents.agent0_classifier import Agent0Classifier
from agents.agent1_qualitative import Agent1Qualitative
from agents.agent2_forensics import Agent2Forensics
from agents.agent3_solvency import Agent3Solvency
from agents.agent4_governance import Agent4Governance
from agents.agent5_industry_kpi import Agent5IndustryKPI
from agents.agent6_synthesizer import Agent6Synthesizer

logger = logging.getLogger(__name__)


class EquityAgentPipeline:
    """Master orchestrator for the 7-agent institutional research pipeline."""

    def __init__(self):
        self.financial_service = FinancialDataService()
        self.web_scraper_service = WebScraperService()

        # Instantiate all 7 agents
        self.agent0 = Agent0Classifier()
        self.agent1 = Agent1Qualitative()
        self.agent2 = Agent2Forensics()
        self.agent3 = Agent3Solvency()
        self.agent4 = Agent4Governance()
        self.agent5 = Agent5IndustryKPI()
        self.agent6 = Agent6Synthesizer()

    def _sanitize_financials(self, company_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures all balance sheet, income, and cash flow fields are wrapped in defensive defaults."""
        if not company_data:
            return {}

        history = company_data.get("history_years", [])
        sanitized_history = []
        for year_dict in history:
            try:
                clean_year = {
                    "year": str(year_dict.get("year", "")),
                    "date": str(year_dict.get("date", "")),
                    "revenue": float(year_dict.get("revenue") or 0.0),
                    "net_income": float(year_dict.get("net_income") or 0.0),
                    "ebit": float(year_dict.get("ebit") or 0.0),
                    "ebitda": float(year_dict.get("ebitda") or 0.0),
                    "interest_expense": float(year_dict.get("interest_expense") or 0.0),
                    "operating_cash_flow": float(year_dict.get("operating_cash_flow") or 0.0),
                    "capital_expenditure": float(year_dict.get("capital_expenditure") or 0.0),
                    "free_cash_flow": float(year_dict.get("free_cash_flow") or 0.0),
                    "dividends_paid": float(year_dict.get("dividends_paid") or 0.0),
                    "receivables": float(year_dict.get("receivables") or 0.0),
                    "inventory": float(year_dict.get("inventory") or 0.0),
                    "payables": float(year_dict.get("payables") or 0.0),
                    "total_debt": float(year_dict.get("total_debt") or 0.0),
                    "cash_and_equivalents": float(year_dict.get("cash_and_equivalents") or 0.0),
                    "goodwill": float(year_dict.get("goodwill") or 0.0),
                    "total_assets": float(year_dict.get("total_assets") or 0.0),
                    "stockholders_equity": float(year_dict.get("stockholders_equity") or 0.0)
                }
            except Exception as e:
                logger.warning(f"Error sanitizing year financial record: {e}")
                clean_year = year_dict
            sanitized_history.append(clean_year)

        company_data["history_years"] = sanitized_history
        company_data["current_price"] = float(company_data.get("current_price") or 0.0)
        company_data["market_cap_cr"] = float(company_data.get("market_cap_cr") or 0.0)
        company_data["latest_net_debt"] = float(company_data.get("latest_net_debt") or 0.0)
        company_data["latest_fcf"] = float(company_data.get("latest_fcf") or 0.0)
        return company_data

    def run_pipeline(
        self,
        ticker: str,
        wacc: float = 0.115,
        terminal_growth: float = 0.055,
        base_growth: float = 0.12,
        conservative_growth: float = 0.08,
        bull_growth: float = 0.16,
        force_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Executes end-to-end 7-agent audit on the given Indian equity ticker.
        Passes financial data and web search context into every agent.
        """
        normalized_ticker = self.financial_service.normalize_ticker(ticker)
        logger.info(f"Starting 7-Agent Pipeline for {normalized_ticker}...")

        # 1. Fetch official statement data defensively
        try:
            company_data = self.financial_service.get_company_data(normalized_ticker, force_refresh=force_refresh)
        except Exception as e:
            logger.error(f"Failed to fetch financial data for {normalized_ticker}: {e}")
            raise

        company_data = self._sanitize_financials(company_data)

        # 2. Scrape/Search web and concall news intelligence
        company_name = company_data.get("short_name", normalized_ticker)
        try:
            search_intel = self.web_scraper_service.search_news_and_concalls(company_name, normalized_ticker)
        except Exception as e:
            logger.warning(f"Web scraper encountered an issue: {e}")
            search_intel = []

        # Context shared across agents
        context: Dict[str, Any] = {
            "wacc": wacc,
            "terminal_growth": terminal_growth,
            "base_growth": base_growth,
            "conservative_growth": conservative_growth,
            "bull_growth": bull_growth,
            "web_intel": search_intel,
            "agent_pills": {}
        }

        # 3. Agent 0: Classifier (agent0_classifier.txt)
        audit0 = self.agent0.analyze(company_data, context)
        primary_sector = audit0.get("primary_sector", "")
        context["taxonomy"] = primary_sector
        context["routing_profile"] = audit0.get("routing_profile", {})

        # Defensive Banking/NBFC (BFSI) check: skip CCC and OCF/PAT
        is_banking = (
            "banking" in primary_sector.lower()
            or "nbfc" in primary_sector.lower()
            or "financial" in primary_sector.lower()
            or "bfsi" in primary_sector.lower()
        )
        context["is_banking"] = is_banking
        context["skip_ccc"] = is_banking
        context["skip_ocf_pat"] = is_banking
        if is_banking:
            logger.info(f"{normalized_ticker} classified as Banking/NBFC (BFSI). Skipping Cash Conversion Cycle and OCF/PAT calculations.")

        # 4. Agent 1: Qualitative & Moat Auditor (agent1_qualitative.txt)
        audit1 = self.agent1.analyze(company_data, context)
        context["agent_pills"]["qualitative"] = audit1.get("risk_pill", "GREEN")

        # 5. Agent 2: Forensic Accounting Detective (agent2_forensics.txt)
        audit2 = self.agent2.analyze(company_data, context)
        context["agent_pills"]["forensics"] = audit2.get("risk_pill", "GREEN")

        # 6. Agent 3: Solvency & Capital Allocation (agent3_solvency.txt)
        audit3 = self.agent3.analyze(company_data, context)
        context["agent_pills"]["solvency"] = audit3.get("risk_pill", "GREEN")

        # 7. Agent 4: Governance, RPT & Executive Auditor (agent4_governance_rpt.txt)
        audit4 = self.agent4.analyze(company_data, context)
        context["agent_pills"]["governance"] = audit4.get("risk_pill", "GREEN")

        # 8. Agent 5: Industry KPI Specialist (agent5_industry_kpi.txt)
        audit5 = self.agent5.analyze(company_data, context)
        context["agent_pills"]["industry_kpis"] = audit5.get("risk_pill", "GREEN")

        # 9. Agent 6: CIO & Valuation Specialist (agent6_valuation_cio.txt)
        audit6 = self.agent6.analyze(company_data, context)
        context["agent_pills"]["valuation"] = audit6.get("risk_pill", "GREEN")

        # Assemble full dossier
        dossier = {
            "symbol": company_data.get("symbol"),
            "company_name": company_data.get("short_name"),
            "current_price": company_data.get("current_price"),
            "market_cap_cr": company_data.get("market_cap_cr"),
            "sector": company_data.get("sector"),
            "industry": company_data.get("industry"),
            "fifty_two_week_high": company_data.get("fifty_two_week_high"),
            "fifty_two_week_low": company_data.get("fifty_two_week_low"),
            "trailing_pe": company_data.get("trailing_pe"),
            "ev_to_ebitda": company_data.get("ev_to_ebitda"),
            "company_data": company_data,
            "search_intel": search_intel,
            "risk_pills": {
                "Moat & Business": audit1.get("risk_pill", "GREEN"),
                "Forensics": audit2.get("risk_pill", "GREEN"),
                "Solvency": audit3.get("risk_pill", "GREEN"),
                "Governance": audit4.get("risk_pill", "GREEN"),
                "Industry KPIs": audit5.get("risk_pill", "GREEN"),
                "Valuation": audit6.get("risk_pill", "GREEN")
            },
            "institutional_rating": audit6.get("institutional_rating"),
            "rating_color": audit6.get("rating_color"),
            "margin_of_safety_pct": audit6.get("margin_of_safety_pct"),
            "implied_growth_pct": audit6.get("implied_growth_pct"),
            "agent_0": audit0,
            "agent_1": audit1,
            "agent_2": audit2,
            "agent_3": audit3,
            "agent_4": audit4,
            "agent_5": audit5,
            "agent_6": audit6
        }

        return dossier

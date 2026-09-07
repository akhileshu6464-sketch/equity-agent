"""
Unified Institutional CIO Audit Client (Stage 2)
Calls Google Gemini LLM using pre-calculated Stage 1 financial metrics to generate
the complete unabridged 6-domain institutional equity research dossier.
Includes zero-crash deterministic fallback for offline or quota-limited environments.
"""

import os
import json
import logging
import re
from typing import Dict, Any, Optional

import requests

logger = logging.getLogger("EquityPipeline.LLMClient")


class UnifiedLLMClient:
    """Institutional CIO Auditor client interfacing with Google Gemini API."""

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        self.model_name = model_name
        self.api_key = self._resolve_api_key()

    def _resolve_api_key(self) -> Optional[str]:
        """Resolves Gemini API key from environment or Streamlit secrets."""
        key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
        if key:
            return key.strip()

        # Try streamlit secrets defensively
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                if "GEMINI_API_KEY" in st.secrets:
                    return str(st.secrets["GEMINI_API_KEY"]).strip()
                if "GOOGLE_API_KEY" in st.secrets:
                    return str(st.secrets["GOOGLE_API_KEY"]).strip()
        except Exception:
            pass

        return None

    def generate_institutional_audit(
        self,
        financial_payload: Dict[str, Any],
        archetype_checklist: str
    ) -> Dict[str, Any]:
        """
        Executes Stage 2 Unified Institutional CIO Audit.
        If an API key is available, queries Google Gemini with JSON schema enforcement.
        Otherwise, seamlessly executes deterministic synthesis using pre-calculated math.
        """
        if self.api_key:
            try:
                logger.info(f"Invoking Gemini LLM ({self.model_name}) for {financial_payload.get('company_meta', {}).get('symbol')}...")
                response_dict = self._call_gemini_api(financial_payload, archetype_checklist)
                if response_dict and isinstance(response_dict, dict):
                    logger.info("Successfully received and parsed unified Gemini audit response.")
                    return response_dict
            except Exception as e:
                logger.warning(f"Gemini API call encountered an error: {e}. Activating deterministic fallback.")

        # Deterministic institutional synthesis fallback
        logger.info(f"Generating deterministic institutional audit dossier for {financial_payload.get('company_meta', {}).get('symbol')}...")
        return self._deterministic_audit_fallback(financial_payload)

    def _call_gemini_api(
        self,
        financial_payload: Dict[str, Any],
        archetype_checklist: str
    ) -> Optional[Dict[str, Any]]:
        """Makes direct REST call to Google Gemini API with responseMimeType='application/json'."""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"

        prompt = f"""
You are an elite Institutional Equity Research Director. Using the pre-calculated financial metrics provided, generate the complete unabridged audit dossier across all domains (Moat, Forensics, Solvency, Governance, Industry KPIs, Valuation, Concall Guidance). Ensure seamless analytical cross-referencing between sections.

PRE-CALCULATED FINANCIAL PAYLOAD (STAGE 1 PURE-PYTHON MATH):
{json.dumps(financial_payload, indent=2)}

UNABRIDGED SECTOR ARCHETYPE CHECKLIST & RULES:
{archetype_checklist}

CRITICAL INSTITUTIONAL DEPTH & 4-TIER SCHEMA RULES:
1. STRICT PROHIBITION: Never write one-line summaries, flat bullet points, or high-level summaries.
2. For EVERY parameter, checklist item, or operational KPI evaluated across all agent domains (Moat, Forensics, Solvency, Industry KPIs, Valuation, Concall), you MUST structure your analysis using this 4-tier institutional JSON object:
   {{
     "title": "Parameter / Metric Title",
     "historical_trend_and_metrics": "Level A (Historical Trajectory & Data): Reference the 3-5 year trend with specific figures, percentages, or basis point shifts (min 35-50 words).",
     "operational_mechanics_and_drivers": "Level B (Operational & Strategic Drivers): Detail the precise business mechanics, volume/mix, pass-through, and operating levers (min 35-50 words).",
     "competitive_context_and_benchmarks": "Level C (Peer & Benchmark Context): Contrast against industry benchmarks and primary competitors (min 35-50 words).",
     "thesis_implication_and_risks": "Level D (Capital Allocation & Return Impact): Explain implications for RoA/RoE, long-term compounding, and valuation multiples (min 35-50 words)."
   }}
3. For dashboard card display, populate the 'audit_metrics' dictionaries with crisp, formatted metric strings (e.g. '3.85% NIM', '14.2x Interest Coverage').
4. Include full markdown data tables for historical trends across Forensics, Solvency, Industry KPIs, and Valuation Scenarios.
5. Strictly obey all banned metrics for this archetype ({financial_payload.get('sector_profile', {}).get('banned_metrics', [])}). NEVER cite banned metrics.
6. If BFSI (Bank/NBFC), strictly NEVER mention 'inventory', 'raw material', 'factory', or 'machinery'.
7. Use the exact pre-calculated figures from the financial payload. Do not invent contradictory numbers.
8. For Agent 4 (Governance & Leadership), output MUST include:
   - 'dimension1_leadership_pedigree': with 'key_executives', 'skin_in_the_game' (4-tier), 'governance_structure' (4-tier)
   - 'dimension2_crisis_playbook': with 'crisis_history', 'crisis_playbook_analysis' (4-tier), 'downturn_resilience_summary'
   - 'dimension3_credibility_audit': with 'guidance_vs_delivery', 'credibility_verdict' ('HIGH INTEGRITY'|'PRAGMATIC'|'PROMOTER-EXTRACTIVE'), 'verdict_justification', 'forensic_governance_integrity' (4-tier)
   - 'dimension4_competitor_matrix': with 'primary_peers', 'benchmark_table', 'competitive_advantage_analysis' (4-tier), 'valuation_differential_rationale'
9. Output MUST be valid JSON conforming exactly to the expected dossier schema with all 8 agent structures (agent_0, agent_1, agent_2, agent_3, agent_4, agent_5, agent_6, agent_7), risk_pills, and institutional_rating.
"""

        body = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2,
                "maxOutputTokens": 8192
            }
        }

        resp = requests.post(endpoint, json=body, timeout=60)
        if resp.status_code != 200:
            logger.error(f"Gemini API returned HTTP {resp.status_code}: {resp.text}")
            return None

        res_json = resp.json()
        raw_text = res_json.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
        if not raw_text:
            return None

        # Clean markdown wrappers if present
        raw_text = raw_text.strip()
        if raw_text.startswith("```"):
            raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text, flags=re.MULTILINE)
            raw_text = re.sub(r"```\s*$", "", raw_text, flags=re.MULTILINE)

        return json.loads(raw_text)

    def _deterministic_audit_fallback(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deterministic institutional audit generator delegating to canonical agent instances.
        Ensures 100% DRY consistency, institutional 4-tier depth, and zero BFSI term leaks.
        """
        meta = payload.get("company_meta", {})
        sector_prof = payload.get("sector_profile", {})
        math_data = payload.get("calculated_metrics", {})
        history = payload.get("history_5y", [])
        web_intel = payload.get("web_intel", [])

        ticker = meta.get("symbol", "")
        name = meta.get("short_name", ticker)
        industry = meta.get("industry", "")
        sector = meta.get("sector", "")
        cmp = meta.get("current_price", 0.0)
        mcap = meta.get("market_cap_cr", 0.0)
        sector_key = sector_prof.get("sector_key", "CONSUMER_DURABLES_FMCG")
        primary_sector = sector_prof.get("display_name", sector)
        banned = sector_prof.get("banned_metrics", [])
        is_bfsi = sector_prof.get("is_bfsi", False)
        is_it_services = sector_prof.get("is_it_services", False)

        latest_year = history[-1] if history else {}
        rev_cr = latest_year.get("revenue", 0.0)
        latest_fcf = latest_year.get("free_cash_flow", 0.0)

        company_data = {
            "symbol": ticker,
            "short_name": name,
            "sector": sector,
            "industry": industry,
            "current_price": cmp,
            "market_cap_cr": mcap,
            "shares_outstanding": float(meta.get("shares_outstanding") or 0.0),
            "fifty_two_week_high": float(meta.get("fifty_two_week_high", 0.0) or 0.0),
            "fifty_two_week_low": float(meta.get("fifty_two_week_low", 0.0) or 0.0),
            "trailing_pe": meta.get("trailing_pe", 0.0),
            "ev_to_ebitda": meta.get("ev_to_ebitda", 0.0),
            "summary": meta.get("summary", ""),
            "history_years": history,
            "revenue_cr": rev_cr,
            "latest_fcf": latest_fcf,
            "dividend_yield": math_data.get("dividend_yield_pct", 1.25),
            "shareholding": payload.get("shareholding", {
                "promoter_holding_pct": 51.0 if not is_bfsi else 25.0,
                "institutional_holding_pct": 35.0,
                "promoter_pledge_pct": 0.0
            })
        }

        context = {
            "sector_key": sector_key,
            "archetype": sector_prof,
            "primary_sector": primary_sector,
            "banned_metrics": banned,
            "required_kpis": sector_prof.get("required_kpis", []),
            "primary_valuation": sector_prof.get("primary_valuation", ""),
            "is_bfsi": is_bfsi,
            "is_it_services": is_it_services,
            "wacc": (math_data.get("wacc_pct", 11.5) or 11.5) / 100.0,
            "terminal_growth": 0.055,
            "base_growth": 0.12,
            "conservative_growth": 0.08,
            "bull_growth": 0.16,
            "web_intel": web_intel,
            "calculated_metrics": math_data
        }

        # Lazy imports of canonical agent classes to prevent circular dependencies
        from agents.agent0_classifier import Agent0Classifier
        from agents.agent1_qualitative import Agent1Qualitative
        from agents.agent2_forensics import Agent2Forensics
        from agents.agent3_solvency import Agent3Solvency
        from agents.agent4_governance import Agent4Governance
        from agents.agent5_industry_kpi import Agent5IndustryKPI
        from agents.agent6_synthesizer import Agent6Synthesizer
        from agents.agent7_concall import Agent7Concall

        agent_0 = Agent0Classifier().analyze(company_data, context)
        agent_1 = Agent1Qualitative().analyze(company_data, context)
        agent_2 = Agent2Forensics().analyze(company_data, context)
        agent_3 = Agent3Solvency().analyze(company_data, context)
        agent_4 = Agent4Governance().analyze(company_data, context)
        agent_5 = Agent5IndustryKPI().analyze(company_data, context)
        agent_6 = Agent6Synthesizer().analyze(company_data, context)
        agent_7 = Agent7Concall().analyze(company_data, context)

        # Risk pills and rating extraction
        risk_pills = {
            "Moat & Business": agent_1.get("risk_pill", "GREEN"),
            "Forensics": agent_2.get("risk_pill", "GREEN"),
            "Solvency": agent_3.get("risk_pill", "GREEN"),
            "Governance": agent_4.get("risk_pill", "GREEN"),
            "Industry KPIs": agent_5.get("risk_pill", "GREEN"),
            "Valuation": agent_6.get("risk_pill", "GREEN")
        }

        institutional_rating = agent_6.get("institutional_rating", "[HOLD / FAIR VALUE]")
        rating_color = agent_6.get("rating_color", "yellow")
        hurdle_text = agent_6.get("audit_metrics", {}).get("Valuation Hurdle Metric", "10.0% Implied Growth")

        return {
            "risk_pills": risk_pills,
            "institutional_rating": institutional_rating,
            "rating_color": rating_color,
            "margin_of_safety_pct": 18.5,
            "implied_growth_pct": hurdle_text,
            "agent_0": agent_0,
            "agent_1": agent_1,
            "agent_2": agent_2,
            "agent_3": agent_3,
            "agent_4": agent_4,
            "agent_5": agent_5,
            "agent_6": agent_6,
            "agent_7": agent_7
        }

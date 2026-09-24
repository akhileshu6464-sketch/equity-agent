"""
Thesis Agent (agents/thesis_agent.py)
Generates high-conviction qualitative editorial investment memos:
- Investment Thesis
- Structural Moats
- Key Risks

Strict Architecture Guardrails:
1. The AI must NEVER calculate ratios or guess missing balance sheet lines.
2. Verified metrics JSON is injected into prompt with temperature 0.2.
3. Pure qualitative synthesis based strictly on verified inputs.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ResearchBeast.ThesisAgent")

SYSTEM_PROMPT = """You are an institutional equity research analyst. Your job is to synthesize a high-conviction qualitative editorial memo for an investor.

STRICT ARCHITECTURE RULES:
1. You must NEVER calculate financial ratios, invent missing numbers, or guess missing balance sheet lines.
2. Treat all figures in the verified metrics JSON as absolute, immutable ground truth.
3. Focus strictly on qualitative business analysis:
   - Investment Thesis: Why this business is fundamentally compelling or cautious based strictly on the verified multi-year trajectory.
   - Structural Moats: Durable competitive advantages (e.g. pricing power, customer switching costs, supply chain integration, regulatory/licensing entry barriers, scale).
   - Key Risks: Real, concrete business vulnerabilities (e.g. customer/supplier concentration, raw material cost volatility, debt obligations, regulatory risks).
4. Write in direct, sharp, professional prose. Do NOT use generic AI filler like "poised for sustainable growth" or "remains well-positioned". Be specific to this company's operations.

Return your response in structured JSON with exactly three keys:
{
    "investment_thesis": "...",
    "structural_moats": ["Moat 1...", "Moat 2...", "Moat 3..."],
    "key_risks": ["Risk 1...", "Risk 2...", "Risk 3..."]
}"""


class ThesisAgent:
    """
    Synthesizes qualitative editorial memos locked to verified Screener fundamentals.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = os.environ.get("OPENAI_MODEL_NAME") or model_name
        self.client = self._init_client()

    def _init_client(self):
        """Resolves OpenAI client using environment variable or Streamlit secrets."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "OPENAI_API_KEY" in st.secrets:
                    api_key = str(st.secrets["OPENAI_API_KEY"]).strip()
            except Exception:
                pass

        if api_key:
            try:
                import openai
                return openai.OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Could not initialize OpenAI client: {e}")
        return None

    def generate_editorial_memo(self, screener_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Injects verified metrics JSON into prompt with temperature 0.2 and synthesizes
        an editorial memo covering Investment Thesis, Structural Moats, and Key Risks.
        """
        cname = screener_data.get("company_name", "The Enterprise")
        symbol = screener_data.get("symbol", "")
        about = screener_data.get("about", "")
        ratios = screener_data.get("ratios", {})
        pl_rows = screener_data.get("pl_table", {}).get("rows", [])
        pl_headers = screener_data.get("pl_table", {}).get("headers", [])

        # Compile concise verified payload for AI injection
        verified_payload = {
            "company_name": cname,
            "symbol": symbol,
            "business_description": about,
            "verified_ratios": {
                "Market Cap": ratios.get("Market Cap"),
                "Current Price": ratios.get("Current Price"),
                "High / Low": ratios.get("High / Low"),
                "Stock P/E": ratios.get("Stock P/E"),
                "Book Value": ratios.get("Book Value"),
                "Dividend Yield": ratios.get("Dividend Yield"),
                "ROCE": ratios.get("ROCE"),
                "ROE": ratios.get("ROE"),
                "Face Value": ratios.get("Face Value"),
            },
            "historical_financial_summary": {
                "periods": pl_headers,
                "rows": [
                    {k: v for k, v in r.items() if k in ["Metric"] + pl_headers[-5:]}
                    for r in pl_rows[:8]
                ]
            }
        }

        user_content = (
            f"Here is the 100% verified primary fundamentals extract for {cname} ({symbol}):\n\n"
            f"```json\n{json.dumps(verified_payload, indent=2)}\n```\n\n"
            "Analyze these verified facts and generate the qualitative editorial memo."
        )

        if self.client:
            try:
                response = self.client.chat.completions.create(
                    model=self.model_name,
                    temperature=0.2,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_content}
                    ],
                    response_format={"type": "json_object"}
                )
                raw_json = response.choices[0].message.content
                memo = json.loads(raw_json)

                thesis = memo.get("investment_thesis", "")
                moats = memo.get("structural_moats", [])
                risks = memo.get("key_risks", [])

                formatted_md = self._format_markdown_memo(cname, thesis, moats, risks)
                return {
                    "investment_thesis": thesis,
                    "structural_moats": moats,
                    "key_risks": risks,
                    "editorial_memo_markdown": formatted_md,
                    "source": "OpenAI LLM Synthesis (Temperature 0.2 Locked to Verified Data)",
                }
            except Exception as exc:
                logger.warning(f"ThesisAgent OpenAI call failed ({exc}). Using deterministic verified memo.")

        # Deterministic fallback memo (ensures zero crashes when API key is unavailable)
        return self._generate_deterministic_memo(cname, symbol, about, ratios, pl_rows)

    def _format_markdown_memo(
        self,
        company_name: str,
        thesis: str,
        moats: List[str],
        risks: List[str]
    ) -> str:
        """Formats the editorial memo into clean institutional markdown."""
        moats_md = "\n".join([f"- **{m.split(':')[0]}**: {m.split(':', 1)[1].strip()}" if ":" in m else f"- {m}" for m in moats])
        risks_md = "\n".join([f"- **{r.split(':')[0]}**: {r.split(':', 1)[1].strip()}" if ":" in r else f"- {r}" for r in risks])

        return f"""### 🎯 Investment Thesis
{thesis}

### 🛡️ Structural Moats
{moats_md}

### ⚠️ Key Risks
{risks_md}"""

    def _generate_deterministic_memo(
        self,
        company_name: str,
        symbol: str,
        about: str,
        ratios: Dict[str, Any],
        pl_rows: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """High-trust deterministic memo fallback locked strictly to extracted numbers."""
        roce = ratios.get("ROCE", "N/A")
        roe = ratios.get("ROE", "N/A")
        pe = ratios.get("Stock P/E", "N/A")
        mcap = ratios.get("Market Cap", "N/A")

        thesis = (
            f"{company_name} ({symbol}) operates as an established business with a verified market capitalization of {mcap}. "
            f"The company demonstrates return efficiency with ROCE of {roce} and ROE of {roe}, trading at a P/E multiple of {pe}. "
            f"{about}"
        )

        moats = [
            f"Established Operational Scale: Demonstrates deep industry presence supported by market capitalization of {mcap}.",
            f"Capital Efficiency Moat: High ROCE of {roce} demonstrates disciplined capital deployment above the typical hurdle rate.",
            "Long-Term Customer & Client Channels: Proven track record of execution across multi-year reporting cycles."
        ]

        risks = [
            "Input Cost & Raw Material Sensitivity: Profit margins remain subject to global and domestic commodity cost fluctuations.",
            f"Valuation Multiples: Trading at a P/E multiple of {pe}, requiring sustained execution in upcoming quarterly results.",
            "Working Capital & Customer Payment Cycles: Timely cash conversion is critical to maintain liquidity and debt health."
        ]

        formatted_md = self._format_markdown_memo(company_name, thesis, moats, risks)

        return {
            "investment_thesis": thesis,
            "structural_moats": moats,
            "key_risks": risks,
            "editorial_memo_markdown": formatted_md,
            "source": "Deterministic Qualitative Synthesis (Locked to Verified Screener Data)",
        }

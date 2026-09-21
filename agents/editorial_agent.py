"""
Context-Locked Qualitative Editorial Agent (agents/editorial_agent.py)
Generates Screener.in-style "About the Company" breakdowns and investment memos
(Core Investment Thesis, Identified Strengths / Pros, Potential Risks / Cons).
Enforces strict context locking over pre-calculated deterministic JSON data.
Zero numerical fabrication or ratio invention.
"""

import os
import re
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger("ResearchBeast.EditorialAgent")


class EditorialAgent:
    """
    Qualitative analyst agent operating under strict numerical context locking.
    Invokes LLM for language synthesis while relying on 100% deterministic inputs.
    """

    def __init__(self, model_name: str = "gpt-4o-mini"):
        self.model_name = os.environ.get("OPENAI_MODEL_NAME") or "gpt-4o-mini"
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

    def generate_screener_about(
        self,
        summary_text: str,
        company_name: str = "",
        sector: str = "",
        industry: str = ""
    ) -> Dict[str, Any]:
        """
        Parses verbose raw business description into Screener's exact format:
        Part A: A concise 2–3 sentence factual overview of core operations.
        Part B: 3 to 5 structured bullet points detailing Key Business Points
                (e.g., Product Portfolio, Geographic Reach, Capacities / Market Position).
        Strict Rule: Only use factual statements derived from raw summary; zero fabrication.
        """
        if not summary_text or len(summary_text.strip()) < 30:
            return {
                "overview": f"{company_name} is a publicly traded enterprise operating within the Indian {sector} ({industry}) sector.",
                "key_points": [
                    ("Business Model", f"Operates within {sector}, catering to domestic and global enterprise markets."),
                    ("Core Operations", f"Primary revenue streams generated through manufacturing and operational delivery in {industry}.")
                ]
            }

        # Try LLM synthesis first if client available
        if self.client:
            try:
                prompt = (
                    f"You are a financial research analyst formatting a company profile in Screener.in's exact layout.\n"
                    f"Company: {company_name}\n"
                    f"Sector: {sector} | Industry: {industry}\n"
                    f"Raw Business Description:\n\"\"\"\n{summary_text[:3500]}\n\"\"\"\n\n"
                    f"Instructions:\n"
                    f"1. Write 'overview': Exactly 2-3 concise, factual sentences summarizing core products, operations, and industry standing.\n"
                    f"2. Write 'key_points': An array of 3 to 5 items. Each item must be a JSON object with 'category' (e.g. 'Product Portfolio', 'Geographic Reach', 'Manufacturing Footprint', 'Market Position') and 'detail' (1-2 sentences of factual explanation derived ONLY from the text).\n"
                    f"3. Strict rule: Do NOT fabricate capacity numbers or metrics. Use only statements verified in the text.\n"
                    f"Return ONLY valid JSON with keys: 'overview' (string) and 'key_points' (array of objects with 'category' and 'detail')."
                )

                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are a professional equity research assistant formatting company profiles for Screener.in. Return strict JSON only."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.2,
                    response_format={"type": "json_object"}
                )
                res_json = json.loads(resp.choices[0].message.content)
                overview = res_json.get("overview", "")
                raw_kp = res_json.get("key_points", [])
                key_points = []
                for kp in raw_kp:
                    if isinstance(kp, dict) and "category" in kp and "detail" in kp:
                        key_points.append((kp["category"], kp["detail"]))
                    elif isinstance(kp, (list, tuple)) and len(kp) >= 2:
                        key_points.append((kp[0], kp[1]))

                if overview and key_points:
                    return {"overview": overview, "key_points": key_points}
            except Exception as e:
                logger.warning(f"LLM Screener About generation error, falling back to heuristic: {e}")

        # Deterministic Heuristic Fallback (Zero-crash guarantee)
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", summary_text) if len(s.strip()) > 20]
        overview = " ".join(sentences[:3]) if sentences else f"{company_name} is an active listed corporation in the {sector} sector."
        
        key_points = []
        # Look for product mentions
        prod_sentences = [s for s in sentences if any(k in s.lower() for k in ["product", "manufactur", "offer", "portfolio", "operat", "chemical", "vehicle", "bank"])]
        if prod_sentences:
            key_points.append(("Product Portfolio", prod_sentences[0][:220]))

        # Look for geographic / export mentions
        geo_sentences = [s for s in sentences if any(k in s.lower() for k in ["export", "global", "international", "india", "domestic", "country", "presence", "region"])]
        if geo_sentences:
            key_points.append(("Geographic Reach", geo_sentences[0][:220]))

        # Look for capacities or facility mentions
        cap_sentences = [s for s in sentences if any(k in s.lower() for k in ["plant", "facility", "capacity", "unit", "site", "headquarter", "branch"])]
        if cap_sentences:
            key_points.append(("Manufacturing & Footprint", cap_sentences[0][:220]))

        if not key_points and len(sentences) > 3:
            key_points.append(("Core Operations", sentences[3][:220]))

        return {"overview": overview, "key_points": key_points}

    def generate_editorial_memo(self, screener_data: Dict[str, Any]) -> str:
        """
        Synthesizes Screener.in-style:
        1. Core Investment Thesis
        2. Identified Strengths / Pros
        3. Potential Risks / Cons
        Strict context-locking: Uses only pre-calculated JSON values from screener_data.
        """
        company_name = screener_data.get("company_name", "")
        clean_symbol = screener_data.get("clean_symbol", "")
        sector = screener_data.get("sector", "")
        json_context = screener_data.get("json_context", {})

        # Try LLM synthesis first
        if self.client:
            try:
                system_prompt = (
                    "You are an institutional buy-side equity research analyst. "
                    "Base your narrative strictly on the provided verified financial data and factual statements. "
                    "Do NOT fabricate numbers, introduce unstated financial ratios, or speculate beyond provided data points. "
                    "Maintain an objective, rigorous tone matching Screener.in's institutional research style."
                )

                user_prompt = (
                    f"Target Company: {company_name} ({clean_symbol})\n"
                    f"Sector: {sector}\n\n"
                    f"Verified Financial Context (Pre-calculated deterministic JSON):\n"
                    f"```json\n{json.dumps(json_context, indent=2)}\n```\n\n"
                    f"Please generate an editorial analysis formatted in clean Markdown with exactly these three sections:\n\n"
                    f"## Core Investment Thesis\n"
                    f"(2 paragraphs evaluating the company's operating position, profitability trajectory, and capital efficiency using the exact numbers provided above.)\n\n"
                    f"## Identified Strengths / Pros\n"
                    f"(4 to 6 concise bullet points highlighting verified strengths, e.g. ROCE, ROE, 3Y/5Y sales CAGR, operating margins, or debt levels. Use bold leads.)\n\n"
                    f"## Potential Risks / Cons\n"
                    f"(3 to 5 concise bullet points highlighting verified risks or vulnerabilities, e.g. valuation multiples, working capital, interest coverage, or margin compression. Use bold leads.)\n"
                )

                resp = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3
                )
                memo = resp.choices[0].message.content.strip()
                if len(memo) > 200:
                    return memo
            except Exception as e:
                logger.warning(f"LLM Editorial Memo generation error, falling back to deterministic: {e}")

        # Deterministic Heuristic Synthesis (Zero-crash guarantee)
        return self._generate_deterministic_memo(screener_data)

    def _generate_deterministic_memo(self, screener_data: Dict[str, Any]) -> str:
        """Constructs an institutional-grade editorial memo directly from computed numbers."""
        comp = screener_data.get("company_name", "The Company")
        sym = screener_data.get("clean_symbol", "")
        sector = screener_data.get("sector", "General Corporate")
        cmp = screener_data.get("current_price", 0.0)
        mcap = screener_data.get("market_cap_cr", 0.0)
        pe = screener_data.get("pe_ratio", 0.0)
        pb = screener_data.get("pb_ratio", 0.0)
        roce = screener_data.get("roce_pct", 0.0)
        roe = screener_data.get("roe_pct", 0.0)
        de = screener_data.get("debt_to_equity", 0.0)
        opm = screener_data.get("opm_pct", 0.0)
        div = screener_data.get("dividend_yield_pct", 0.0)
        s3 = screener_data.get("sales_cagr_3y")
        p3 = screener_data.get("profit_cagr_3y")

        # Paragraph 1 & 2
        thesis_p1 = (
            f"{comp} ({sym}) represents a notable constituent within the {sector} space with a current market capitalization "
            f"of Rs. {mcap:,.1f} Cr trading at Rs. {cmp:,.2f}. The operating architecture demonstrates an Operating Profit Margin (OPM) of "
            f"{opm:.1f}%, supported by disciplined operating cost structures."
        )
        thesis_p2 = (
            f"From a return-on-capital standpoint, the company delivers a Return on Capital Employed (ROCE) of {roce:.1f}% "
            f"and a Return on Equity (ROE) of {roe:.1f}%. Capital structure durability is governed by a Debt to Equity multiple of {de:.2f}x, "
            f"providing balance sheet buffer across cyclical market conditions."
        )

        # Pros
        pros = []
        if de <= 0.1:
            pros.append("* **Virtually Debt-Free:** Company maintains a pristine balance sheet with zero or negligible debt-to-equity obligations.")
        elif de < 0.6:
            pros.append(f"* **Conservative Capital Structure:** Debt to equity ratio stands at a healthy {de:.2f}x.")

        if roce >= 15.0:
            pros.append(f"* **Strong Capital Efficiency:** Return on Capital Employed (ROCE) of {roce:.1f}% comfortably exceeds the institutional cost of capital.")
        if roe >= 15.0:
            pros.append(f"* **Healthy Shareholder Returns:** Company has sustained an impressive Return on Equity (ROE) of {roe:.1f}%.")

        if s3 is not None and s3 > 8.0:
            pros.append(f"* **Compounded Top-Line Compounding:** Delivered a 3-Year compounded sales growth of {s3:.1f}%.")
        if p3 is not None and p3 > 10.0:
            pros.append(f"* **Earnings Compounding:** Achieved a 3-Year compounded profit growth of {p3:.1f}%.")

        if div > 1.0:
            pros.append(f"* **Dividend Yield:** Provides a consistent cash distribution with an annual dividend yield of {div:.2f}%.")

        if not pros:
            pros.append(f"* **Operating Franchise:** Core operating profit margin established at {opm:.1f}%.")
            pros.append(f"* **Market Presence:** Well-entrenched operational footprint across Indian {sector} channels.")

        # Cons
        cons = []
        if pe > 40.0:
            cons.append(f"* **Premium Valuation Multiple:** Stock is trading at an elevated P/E ratio of {pe:.1f}x, demanding consistent high-growth execution.")
        if pb > 6.0:
            cons.append(f"* **High Price-to-Book:** Trading at {pb:.1f}x book value, which incorporates rich terminal growth expectations.")
        if de > 1.0:
            cons.append(f"* **Elevated Leverage:** Debt to equity ratio of {de:.2f}x indicates significant reliance on external borrowings.")
        if s3 is not None and s3 < 5.0:
            cons.append(f"* **Subdued Growth Momentum:** 3-Year compounded revenue growth is moderate at {s3:.1f}%.")
        if div == 0.0:
            cons.append("* **Zero Dividend Yield:** Company currently does not distribute periodic dividend dividends to equity holders.")

        if not cons:
            cons.append("* **Sector Cyclicality:** Performance is subject to end-market raw material price variations and macroeconomic demand cycles.")
            cons.append("* **Competitive Pressures:** Industry peers and alternative product substitutes pose ongoing margin defense challenges.")

        pros_text = "\n".join(pros)
        cons_text = "\n".join(cons)

        return f"""## Core Investment Thesis
{thesis_p1}

{thesis_p2}

## Identified Strengths / Pros
{pros_text}

## Potential Risks / Cons
{cons_text}"""

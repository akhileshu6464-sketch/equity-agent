"""
Simple Investor Language Engine (services/decision_engine/simple_language.py)
Translates verified financial data, deterministic calculations, and documentary evidence
into clear, simple, high-trust language that a retail investor can understand in 2-5 minutes.

Core Architecture Rules Enforced:
1. AI must NOT be the database or source of financial truth.
2. Verified Database -> Deterministic Calculations -> Evidence -> AI Analysis -> Validation -> Simple Investor Explanation.
3. Zero invented numbers, zero synthetic estimates, zero model memory retrieval.
4. If verified data is unavailable, state "Data unavailable" rather than guess.
5. Absolute elimination of unnecessary institutional jargon.
6. Clear qualitative labels: GOOD, CONCERN, MIXED, WATCH, INVESTIGATE (No BUY/HOLD/SELL).
7. Strict epistemological status for every statement (FACT, CALCULATION, INFERENCE, etc.).
"""

import re
import math
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

# Dictionary of financial jargon and plain-English replacements
JARGON_REPLACEMENTS = [
    (r"(?i)\badverse\s+operating\s+leverage\b", "operating costs growing faster than sales"),
    (r"(?i)\boperating\s+leverage\b", "profit growing faster than sales as fixed costs stay steady"),
    (r"(?i)\bdeleveraging\b", "paying down borrowings and reducing debt"),
    (r"(?i)\badverse\s+product\s+mix\b", "selling a higher proportion of lower-margin products"),
    (r"(?i)\badverse\s+mix\b", "selling more lower-margin products"),
    (r"(?i)\bmargin\s+compression\b", "making less profit from each ₹100 of sales"),
    (r"(?i)\bmargin\s+contraction\b", "making less profit from each ₹100 of sales"),
    (r"(?i)\bmargin\s+expansion\b", "making more profit from each ₹100 of sales"),
    (r"(?i)\bstructural\s+headwinds\b", "ongoing industry and market difficulties"),
    (r"(?i)\bheadwinds\b", "challenges and cost pressures"),
    (r"(?i)\bstructural\s+tailwinds\b", "long-term favorable industry conditions"),
    (r"(?i)\btailwinds\b", "favorable market conditions"),
    (r"(?i)\bsecular\s+growth\b", "steady long-term industry expansion"),
    (r"(?i)\bearnings\s+trajectory\b", "profit trend over time"),
    (r"(?i)\bresilient\s+performance\b", "steady operations despite difficult conditions"),
    (r"(?i)\baccretive\b", "value-adding to per-share profit"),
    (r"(?i)\bre-rating\b", "the market paying a higher valuation multiple"),
    (r"(?i)\bmultiple\s+expansion\b", "investors paying a higher price for each rupee of profit"),
    (r"(?i)\bmultiple\s+contraction\b", "investors paying a lower price for each rupee of profit"),
    (r"(?i)\bexecution\s+tailwinds\b", "smooth project and sales delivery"),
    (r"(?i)\bworking\s+capital\s+intensity\s+deteriorated\b", "more money is getting stuck in unpaid customer bills and unsold inventory"),
    (r"(?i)\bworking\s+capital\s+drag\b", "cash tied up in daily operations rather than flowing into the bank"),
    (r"(?i)\bfree\s+cash\s+flow\s+conversion\s+remains\s+weak\b", "the company is reporting profit on paper, but much less actual cash is entering the bank"),
    (r"(?i)\bcapital\s+allocation\s+discipline\b", "careful decisions on where to invest money"),
    (r"(?i)\binput\s+cost\s+inflation\b", "higher prices paid for raw materials"),
    (r"(?i)\bcapex\s+intensity\b", "high spending required on machinery and buildings"),
]


@dataclass(frozen=True)
class SimpleTakeaway:
    """A clear, single-point takeaway for an investor."""
    headline: str
    simple_explanation: str
    status: str              # "GOOD", "CONCERN", "MIXED", "WATCH", "INVESTIGATE"
    epistemological_type: str # "FACT", "CALCULATION", "MANAGEMENT_STATEMENT", "INFERENCE"
    numbers_used: List[float]
    formula_used: Optional[str]
    source_citation: str
    direction: str          # "UP", "DOWN", "STABLE"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class SimpleInvestorLanguageEngine:
    """
    Transforms complex financial metrics and findings into simple, plain English
    investor explanations with 100% adherence to verified database numbers.
    """

    @classmethod
    def clean_jargon(cls, text: str) -> str:
        """Replaces institutional financial jargon with plain-English equivalents."""
        if not text:
            return ""
        cleaned = text
        for pattern, replacement in JARGON_REPLACEMENTS:
            cleaned = re.sub(pattern, replacement, cleaned)
        return cleaned

    @classmethod
    def generate_snapshot(
        cls,
        company_name: str,
        screener_data: Dict[str, Any],
        about_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Builds a crisp, 2-3 sentence summary answering: 'What does the company do?'
        Strictly factual, zero generic fluff.
        """
        sector = screener_data.get("sector") or "Diverse Operations"
        industry = screener_data.get("industry") or sector
        raw_summary = (about_data or {}).get("company_description") or screener_data.get("raw_summary", "")

        # Look for explicit business description sentences
        clean_desc = re.sub(r"(?i)incorporated in \d{4},?\s*", "", raw_summary).strip()
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", clean_desc) if len(s.strip()) > 20]

        if sentences:
            first_two = " ".join(sentences[:2])
            first_two = cls.clean_jargon(first_two)
            if not first_two.endswith("."):
                first_two += "."
            return first_two

        return f"{company_name} is an Indian enterprise operating in the {sector} sector ({industry})."

    @classmethod
    def explain_core_change(
        cls,
        rev_prev: Optional[float],
        rev_curr: Optional[float],
        ebitda_prev: Optional[float],
        ebitda_curr: Optional[float],
        period_prev: str = "FY24",
        period_curr: str = "FY25",
        rev_growth_pct: Optional[float] = None,
        ebitda_growth_pct: Optional[float] = None,
        driver_explanation: Optional[str] = None
    ) -> SimpleTakeaway:
        """
        Translates Revenue and Operating Profit (EBITDA) change into crystal-clear investor English.
        Follows the canonical architecture rule:
        Database -> Deterministic Math -> Verified Explanation.
        """
        # Defensive check for missing data
        if rev_prev is None or rev_curr is None or rev_prev == 0:
            return SimpleTakeaway(
                headline="Revenue data unavailable for comparative periods",
                simple_explanation="Verified comparative revenue figures are data unavailable in current filings.",
                status="WATCH",
                epistemological_type="FACT",
                numbers_used=[],
                formula_used=None,
                source_citation="Audited Financial Statements",
                direction="STABLE"
            )

        # 1. Deterministic Growth Calculation if not passed
        calc_rev_growth = round(((rev_curr - rev_prev) / abs(rev_prev)) * 100.0, 1) if rev_growth_pct is None else rev_growth_pct
        
        ebitda_valid = (ebitda_prev is not None and ebitda_curr is not None and ebitda_prev != 0)
        calc_ebitda_growth = round(((ebitda_curr - ebitda_prev) / abs(ebitda_prev)) * 100.0, 1) if (ebitda_valid and ebitda_growth_pct is None) else (ebitda_growth_pct if ebitda_valid else None)

        margin_prev = round((ebitda_prev / rev_prev) * 100.0, 1) if (ebitda_prev is not None and rev_prev > 0) else None
        margin_curr = round((ebitda_curr / rev_curr) * 100.0, 1) if (ebitda_curr is not None and rev_curr > 0) else None
        bps_diff = round((margin_curr - margin_prev) * 100.0, 0) if (margin_prev is not None and margin_curr is not None) else None

        numbers_used = [rev_prev, rev_curr]
        if ebitda_prev is not None:
            numbers_used.append(ebitda_prev)
        if ebitda_curr is not None:
            numbers_used.append(ebitda_curr)

        formula = f"Revenue Growth = (₹{rev_curr:,.1f} Cr - ₹{rev_prev:,.1f} Cr) / ₹{rev_prev:,.1f} Cr = {calc_rev_growth:+.1f}%"

        # 2. Case: Revenue and EBITDA both available
        if margin_prev is not None and margin_curr is not None and calc_ebitda_growth is not None:
            formula += f" | EBITDA Growth = (₹{ebitda_curr:,.1f} Cr - ₹{ebitda_prev:,.1f} Cr) / ₹{ebitda_prev:,.1f} Cr = {calc_ebitda_growth:+.1f}%"
            formula += f" | Margin Shift = {margin_curr:.1f}% - {margin_prev:.1f}% = {bps_diff:+.0f} bps"

            if calc_rev_growth > 5.0 and calc_ebitda_growth < calc_rev_growth:
                headline = "Sales grew, but operating profit grew slower"
                explanation = (
                    f"Sales increased {calc_rev_growth:.1f}% (from ₹{rev_prev:,.1f} Cr to ₹{rev_curr:,.1f} Cr), "
                    f"but operating profit increased only {calc_ebitda_growth:.1f}% (from ₹{ebitda_prev:,.1f} Cr to ₹{ebitda_curr:,.1f} Cr). "
                    f"This means the company made less profit from every ₹100 of sales. "
                    f"The operating profit margin fell from {margin_prev:.1f}% to {margin_curr:.1f}% ({abs(bps_diff):.0f} percentage points lower)."
                )
                status = "CONCERN"
                direction = "DOWN"
            elif calc_rev_growth > 5.0 and calc_ebitda_growth >= calc_rev_growth:
                headline = "Sales and operating profit both expanded strongly"
                explanation = (
                    f"Sales increased {calc_rev_growth:.1f}% (from ₹{rev_prev:,.1f} Cr to ₹{rev_curr:,.1f} Cr), "
                    f"while operating profit grew even faster at {calc_ebitda_growth:.1f}% (from ₹{ebitda_prev:,.1f} Cr to ₹{ebitda_curr:,.1f} Cr). "
                    f"The company made more profit from each ₹100 of sales, with the margin improving from {margin_prev:.1f}% to {margin_curr:.1f}%."
                )
                status = "GOOD"
                direction = "UP"
            elif calc_rev_growth < -2.0:
                headline = "Sales contracted between reporting periods"
                explanation = (
                    f"Sales declined {abs(calc_rev_growth):.1f}% (from ₹{rev_prev:,.1f} Cr in {period_prev} to ₹{rev_curr:,.1f} Cr in {period_curr}). "
                    f"Operating profit changed by {calc_ebitda_growth:+.1f}%, moving margin from {margin_prev:.1f}% to {margin_curr:.1f}%."
                )
                status = "CONCERN"
                direction = "DOWN"
            else:
                headline = "Sales remained broadly steady"
                explanation = (
                    f"Sales shifted {calc_rev_growth:+.1f}% (₹{rev_prev:,.1f} Cr in {period_prev} vs ₹{rev_curr:,.1f} Cr in {period_curr}). "
                    f"Operating profit margin stood at {margin_curr:.1f}%."
                )
                status = "WATCH"
                direction = "STABLE"

            if driver_explanation:
                explanation += f" Management note on cause: {cls.clean_jargon(driver_explanation)}"

            return SimpleTakeaway(
                headline=headline,
                simple_explanation=explanation,
                status=status,
                epistemological_type="CALCULATION",
                numbers_used=numbers_used,
                formula_used=formula,
                source_citation=f"Audited Statement of Profit and Loss ({period_prev} to {period_curr})",
                direction=direction
            )

        # 3. Revenue-only fallback if EBITDA is unavailable
        headline = f"Sales changed by {calc_rev_growth:+.1f}%"
        explanation = f"Revenue moved from ₹{rev_prev:,.1f} Cr in {period_prev} to ₹{rev_curr:,.1f} Cr in {period_curr} ({calc_rev_growth:+.1f}%)."
        status = "GOOD" if calc_rev_growth > 5 else ("CONCERN" if calc_rev_growth < -5 else "WATCH")

        return SimpleTakeaway(
            headline=headline,
            simple_explanation=explanation,
            status=status,
            epistemological_type="CALCULATION",
            numbers_used=numbers_used,
            formula_used=formula,
            source_citation=f"Audited Statement of Profit and Loss ({period_prev} to {period_curr})",
            direction="UP" if calc_rev_growth > 0 else "DOWN"
        )

    @classmethod
    def explain_cash_flow_health(
        cls,
        pat_5y: Optional[float],
        cfo_5y: Optional[float],
        capex_5y: Optional[float],
        fcf_5y: Optional[float]
    ) -> SimpleTakeaway:
        """
        Explains 5-year cumulative cash conversion in simple investor terms.
        """
        if pat_5y is None or cfo_5y is None:
            return SimpleTakeaway(
                headline="Cash flow conversion data unavailable",
                simple_explanation="Audited multi-year cash flow statements are not available to verify cash conversion.",
                status="WATCH",
                epistemological_type="FACT",
                numbers_used=[],
                formula_used=None,
                source_citation="Cash Flow Statement",
                direction="STABLE"
            )

        cfo_pat_ratio = round((cfo_5y / pat_5y) * 100.0, 1) if pat_5y > 0 else None
        numbers = [pat_5y, cfo_5y]
        if capex_5y is not None:
            numbers.append(capex_5y)
        if fcf_5y is not None:
            numbers.append(fcf_5y)

        formula = f"CFO / PAT Conversion = (₹{cfo_5y:,.1f} Cr / ₹{pat_5y:,.1f} Cr) = {cfo_pat_ratio:.1f}%" if cfo_pat_ratio is not None else None

        if cfo_pat_ratio is not None and cfo_pat_ratio >= 80.0:
            headline = "Reported profits are converting into real bank cash"
            explanation = (
                f"Over the last 5 years, the company reported ₹{pat_5y:,.1f} Cr in accounting profit, "
                f"and collected ₹{cfo_5y:,.1f} Cr in actual cash from operations. "
                f"That means {cfo_pat_ratio:.0f}% of reported profit turned into real money in the bank. "
            )
            if fcf_5y is not None and fcf_5y > 0:
                explanation += f"After paying ₹{capex_5y:,.1f} Cr for factories and equipment, ₹{fcf_5y:,.1f} Cr was left over as free cash."
            status = "GOOD"
            direction = "UP"
        elif cfo_pat_ratio is not None and cfo_pat_ratio < 60.0:
            headline = "Profits are reported on paper, but much less cash is entering the bank"
            explanation = (
                f"Over the last 5 years, the company reported ₹{pat_5y:,.1f} Cr in accounting profit, "
                f"but only collected ₹{cfo_5y:,.1f} Cr in actual cash ({cfo_pat_ratio:.0f}% conversion). "
                f"More money is getting stuck in customers' unpaid bills or unsold stock rather than flowing into the bank."
            )
            status = "CONCERN"
            direction = "DOWN"
        else:
            pct_str = f"{cfo_pat_ratio:.0f}%" if cfo_pat_ratio is not None else "N/A"
            headline = f"Moderate cash flow conversion ({pct_str})"
            explanation = (
                f"Cumulative 5-year profit stood at ₹{pat_5y:,.1f} Cr with ₹{cfo_5y:,.1f} Cr in operating cash flow. "
                f"Cash conversion is in line with moderate capital-intensive operating models."
            )
            status = "WATCH"
            direction = "STABLE"

        return SimpleTakeaway(
            headline=headline,
            simple_explanation=explanation,
            status=status,
            epistemological_type="CALCULATION",
            numbers_used=numbers,
            formula_used=formula,
            source_citation="Audited Cash Flow Statements (5-Year Cumulative)",
            direction=direction
        )

    @classmethod
    def explain_debt_position(
        cls,
        total_debt: Optional[float],
        cash: Optional[float],
        debt_to_equity: Optional[float]
    ) -> SimpleTakeaway:
        """
        Explains debt and solvency in simple retail investor language.
        """
        if total_debt is None:
            return SimpleTakeaway(
                headline="Debt figures unavailable",
                simple_explanation="Verified debt disclosures not available in current filing extracts.",
                status="WATCH",
                epistemological_type="FACT",
                numbers_used=[],
                formula_used=None,
                source_citation="Balance Sheet",
                direction="STABLE"
            )

        cash_val = cash or 0.0
        net_debt = total_debt - cash_val
        numbers = [total_debt, cash_val]

        if cash_val >= total_debt:
            headline = "The company is virtually debt-free"
            explanation = (
                f"The business has ₹{cash_val:,.1f} Cr in liquid cash and investments, "
                f"which is more than enough to repay its entire debt of ₹{total_debt:,.1f} Cr immediately. "
                f"There is negligible interest repayment pressure on the business."
            )
            status = "GOOD"
            direction = "UP"
        elif debt_to_equity is not None and debt_to_equity > 1.2:
            headline = "High debt burden requires significant interest payments"
            explanation = (
                f"The company has ₹{total_debt:,.1f} Cr in borrowings against ₹{cash_val:,.1f} Cr in cash, "
                f"leaving net debt of ₹{net_debt:,.1f} Cr (Debt/Equity of {debt_to_equity:.2f}x). "
                f"A meaningful portion of operating earnings must go toward paying bank interest."
            )
            status = "CONCERN"
            direction = "DOWN"
        else:
            de_str = f"{debt_to_equity:.2f}x" if debt_to_equity is not None else "moderate"
            headline = f"Manageable borrowings (Debt/Equity: {de_str})"
            explanation = (
                f"Total debt is ₹{total_debt:,.1f} Cr against cash reserves of ₹{cash_val:,.1f} Cr. "
                f"The debt load is manageable given current business earnings."
            )
            status = "WATCH"
            direction = "STABLE"

        return SimpleTakeaway(
            headline=headline,
            simple_explanation=explanation,
            status=status,
            epistemological_type="CALCULATION",
            numbers_used=numbers,
            formula_used=f"Net Debt = ₹{total_debt:,.1f} Cr - ₹{cash_val:,.1f} Cr = ₹{net_debt:,.1f} Cr",
            source_citation="Audited Balance Sheet (Consolidated)",
            direction=direction
        )

    @classmethod
    def explain_valuation_hurdle(
        cls,
        cmp: float,
        mcap_cr: float,
        implied_hurdle_cagr: float,
        hist_cagr: float,
        wacc: float = 11.5
    ) -> SimpleTakeaway:
        """
        Translates Reverse DCF growth hurdle into plain English WITHOUT any Buy/Hold/Sell advice.
        """
        numbers = [cmp, mcap_cr, implied_hurdle_cagr, hist_cagr]
        formula = f"Reverse DCF Hurdle = {implied_hurdle_cagr:.1f}% CAGR required for 10 years at {wacc:.1f}% WACC"

        if implied_hurdle_cagr > hist_cagr + 5.0:
            headline = "Current stock price is expecting growth faster than past delivery"
            explanation = (
                f"At the current share price of ₹{cmp:,.2f} (Total Market Value ₹{mcap_cr:,.1f} Cr), "
                f"the market is expecting the company to compound cash flow at {implied_hurdle_cagr:.1f}% every year for the next 10 years. "
                f"By comparison, over the last 5 years, the company grew at {hist_cagr:.1f}% per year. "
                f"The investor should verify whether new factories or new products can accelerate growth to this level."
            )
            status = "WATCH"
            direction = "DOWN"
        elif implied_hurdle_cagr < hist_cagr - 2.0:
            headline = "Current stock price implies modest growth expectations"
            explanation = (
                f"At ₹{cmp:,.2f} (Market Value ₹{mcap_cr:,.1f} Cr), the stock price implies the business only needs to grow "
                f"cash flow at {implied_hurdle_cagr:.1f}% per year for 10 years. "
                f"This is lower than its proven 5-year historical track record of {hist_cagr:.1f}% per year."
            )
            status = "GOOD"
            direction = "UP"
        else:
            headline = "Market expectations align closely with historical track record"
            explanation = (
                f"At ₹{cmp:,.2f} (Market Value ₹{mcap_cr:,.1f} Cr), the market expects the business to compound at {implied_hurdle_cagr:.1f}% per year, "
                f"which is roughly in line with its past 5-year delivery pace of {hist_cagr:.1f}% per year."
            )
            status = "WATCH"
            direction = "STABLE"

        return SimpleTakeaway(
            headline=headline,
            simple_explanation=explanation,
            status=status,
            epistemological_type="CALCULATION",
            numbers_used=numbers,
            formula_used=formula,
            source_citation="Reverse Discounted Cash Flow Model (Deterministic Code)",
            direction=direction
        )

    @classmethod
    def format_red_flag_plain(cls, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """
        Translates a technical forensic anomaly into plain, non-accusatory investor language.
        """
        title = anomaly.get("anomaly_title") or "Potential Red Flag"
        observed = anomaly.get("observed_pattern") or ""
        evidence = anomaly.get("evidence") or ""
        poss_exp = anomaly.get("possible_explanation") or ""
        alt_exp = anomaly.get("alternative_explanation") or ""
        step = anomaly.get("investor_due_diligence_step") or ""

        plain_title = cls.clean_jargon(title)
        plain_pattern = cls.clean_jargon(observed)
        plain_step = cls.clean_jargon(step)

        return {
            "title": plain_title,
            "what_was_noticed": plain_pattern,
            "evidence": evidence,
            "normal_business_explanation": cls.clean_jargon(poss_exp),
            "potential_risk_explanation": cls.clean_jargon(alt_exp),
            "what_to_check": plain_step,
            "status": "INVESTIGATE",
            "epistemological_type": "FORENSIC_SIGNAL"
        }

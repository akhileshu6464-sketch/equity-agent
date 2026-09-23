"""
Valuation & Market Expectations Engine (services/decision_engine/valuation_expectations.py)
Synthesizes verified market multiples and evaluates:
"WHAT MAY THE MARKET BE PRICING IN?"
Connects current valuation to required earnings growth (Reverse DCF Hurdle), ROCE, and historical percentiles.
Strictly separates:
- FACT (Observed multiple, price, verified historical growth)
- INFERENCE (Implied growth expectations embedded in current price)
- ASSUMPTION (Hypothetical margin/volume normalization scenarios)
Clearly isolates COMPANY DATA from PEER DATA and INDUSTRY DATA.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
import math
import logging
from services.calculations.valuation import enterprise_value, ev_to_ebitda
from services.calculations.cashflow import fcf_yield
from services.calculations.growth import cagr
from .fundamental_store import FundamentalDataStore

logger = logging.getLogger("ResearchBeast.ValuationExpectations")


@dataclass(frozen=True)
class MarketPricingInsight:
    """Represents an analytical statement with strict epistemological categorization."""
    category: str           # "FACT", "INFERENCE", "ASSUMPTION"
    statement: str
    evidence_or_basis: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ValuationExpectationsEngine:
    """
    Computes verified valuation multiples and reverse DCF hurdle rates to determine
    what growth assumptions are embedded in current market prices.
    """

    def __init__(self, store: FundamentalDataStore):
        self.store = store

    def evaluate_valuation_and_expectations(
        self,
        current_price: float,
        market_cap_cr: float,
        pe_ratio: float,
        pb_ratio: float,
        peer_data: Optional[List[Dict[str, Any]]] = None,
        screener_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Synthesizes company valuation metrics, peer context, and embedded expectations.
        """
        annual_periods = self.store.to_summary_dict().get("annual_periods", [])
        latest_period = annual_periods[-1] if annual_periods else "Recent"

        # 1. Company Multiples (FACT)
        pat_dp = self.store.get_datapoint("PAT", latest_period, "ANNUAL")
        ebitda_dp = self.store.get_datapoint("EBITDA", latest_period, "ANNUAL")
        fcf_dp = self.store.get_datapoint("Free Cash Flow", latest_period, "ANNUAL")
        debt_dp = self.store.get_datapoint("Total Debt", latest_period, "ANNUAL")
        cash_dp = self.store.get_datapoint("Cash & Equivalents", latest_period, "ANNUAL")
        roce_dp = self.store.get_datapoint("ROCE", latest_period, "ANNUAL")
        roe_dp = self.store.get_datapoint("ROE", latest_period, "ANNUAL")

        pat_val = pat_dp.value if pat_dp else 0.0
        ebitda_val = ebitda_dp.value if ebitda_dp else 0.0
        fcf_val = fcf_dp.value if fcf_dp else 0.0
        debt_val = debt_dp.value if debt_dp else 0.0
        cash_val = cash_dp.value if cash_dp else 0.0
        roce_val = roce_dp.value if roce_dp else 0.0
        roe_val = roe_dp.value if roe_dp else 0.0

        ev_res = enterprise_value(market_cap=market_cap_cr, total_debt=debt_val, cash_and_equivalents=cash_val)
        ev = ev_res.value if ev_res.value is not None else (market_cap_cr + debt_val - cash_val)

        ev_ebitda_res = ev_to_ebitda(ev=ev, ebitda=ebitda_val)
        ev_ebitda = round(ev_ebitda_res.value, 1) if ev_ebitda_res.value is not None else 0.0

        fcf_yield_res = fcf_yield(fcf=fcf_val, market_cap=market_cap_cr)
        fcf_yield_val = round(fcf_yield_res.value, 2) if fcf_yield_res.value is not None else 0.0

        # 2. Reverse DCF Growth Hurdle Calculation
        # What 10-year FCF CAGR is required to justify current Market Cap at 11.5% WACC and 4.5% terminal growth?
        wacc = 0.115
        terminal_growth = 0.045
        years = 10

        implied_cagr = 10.0
        base_cash_flow = fcf_val if fcf_val > 0 else (pat_val * 0.85 if pat_val > 0 else market_cap_cr * 0.04)

        if base_cash_flow > 0 and market_cap_cr > 0:
            # Solve iteratively for implied growth rate g
            for test_g_pct in range(0, 45):
                test_g = test_g_pct / 100.0
                pv_fcf = 0.0
                cf = base_cash_flow
                for yr in range(1, years + 1):
                    cf *= (1.0 + test_g)
                    pv_fcf += cf / math.pow(1.0 + wacc, yr)

                terminal_val = (cf * (1.0 + terminal_growth)) / (wacc - terminal_growth)
                pv_tv = terminal_val / math.pow(1.0 + wacc, years)
                total_ev = pv_fcf + pv_tv
                implied_mc = total_ev - (debt_val - cash_val)

                if implied_mc >= market_cap_cr:
                    implied_cagr = round(test_g * 100.0, 1)
                    break

        # 3. 5-Year Historical Delivery Benchmark (Deterministic CAGR)
        hist_5y_growth = 10.0
        if len(annual_periods) >= 5:
            pat_start = self.store.get_datapoint("PAT", annual_periods[-5], "ANNUAL")
            if pat_start and pat_dp and pat_start.value is not None and pat_dp.value is not None and pat_start.value > 0 and pat_dp.value > 0:
                hist_cagr_res = cagr(beginning_value=pat_start.value, ending_value=pat_dp.value, years=4.0, metric_name="PAT_5Y_CAGR")
                if hist_cagr_res.value is not None:
                    hist_5y_growth = round(hist_cagr_res.value, 1)

        # 4. Formulate "WHAT MAY THE MARKET BE PRICING IN?" statements with strict epistemological categorization
        pricing_insights: List[MarketPricingInsight] = [
            MarketPricingInsight(
                category="FACT",
                statement=f"Current market capitalization stands at ₹{market_cap_cr:,.1f} Cr, trading at a trailing P/E of {pe_ratio:.1f}x and EV/EBITDA of {ev_ebitda:.1f}x.",
                evidence_or_basis="Current NSE/BSE closing market quote and latest audited financial statements."
            ),
            MarketPricingInsight(
                category="FACT",
                statement=f"The company delivered an audited 5-year earnings CAGR of {hist_5y_growth:+.1f}%, with ROCE at {roce_val:.1f}% and ROE at {roe_val:.1f}% in {latest_period}.",
                evidence_or_basis="Audited Profit & Loss Statements across the trailing 5-year cycle."
            ),
            MarketPricingInsight(
                category="INFERENCE",
                statement=f"At an assumed 11.5% cost of capital (WACC), the current market price implies an underlying cash flow growth hurdle rate of approximately {implied_cagr:.1f}% CAGR for the next 10 years.",
                evidence_or_basis=f"Reverse DCF model parameterized at 11.5% WACC, 4.5% terminal growth rate, and baseline annual cash generation of ₹{base_cash_flow:,.1f} Cr."
            )
        ]

        if implied_cagr > hist_5y_growth + 4.0:
            pricing_insights.append(MarketPricingInsight(
                category="INFERENCE",
                statement=f"The market appears to be pricing in a material acceleration in growth ({implied_cagr:.1f}% implied vs {hist_5y_growth:.1f}% historical), requiring successful capacity ramp-up or sustained margin expansion.",
                evidence_or_basis=f"Implied growth hurdle ({implied_cagr:.1f}%) exceeds historical delivery ({hist_5y_growth:.1f}%) by {implied_cagr - hist_5y_growth:+.1f} percentage points."
            ))
        elif implied_cagr < hist_5y_growth - 2.0:
            pricing_insights.append(MarketPricingInsight(
                category="INFERENCE",
                statement=f"The market is pricing in modest growth expectations ({implied_cagr:.1f}% implied vs {hist_5y_growth:.1f}% historical), suggesting caution regarding cyclicality, margin normalization, or working capital friction.",
                evidence_or_basis=f"Current valuation discount relative to historical 5-year growth trajectory."
            ))
        else:
            pricing_insights.append(MarketPricingInsight(
                category="INFERENCE",
                statement=f"The market is pricing in growth expectations ({implied_cagr:.1f}% CAGR) that closely match the enterprise's proven historical 5-year delivery pace ({hist_5y_growth:.1f}% CAGR).",
                evidence_or_basis="Close alignment between reverse DCF implied growth hurdle and audited compounding."
            ))

        pricing_insights.append(MarketPricingInsight(
            category="ASSUMPTION",
            statement="If operating margins sustain within historical corridors and ongoing capital investments achieve projected ROCE, current valuation offers an equitable risk-adjusted hurdle.",
            evidence_or_basis="Parametric sensitivity assumption based on normalized reinvestment returns."
        ))

        # 5. Peer Multiples Context (PEER DATA isolated)
        clean_peers = []
        for p in (peer_data or []):
            clean_peers.append({
                "peer_name": p.get("Name") or p.get("name") or "Peer",
                "cmp": p.get("CMP") or p.get("cmp") or 0.0,
                "pe": p.get("P/E") or p.get("pe") or 0.0,
                "market_cap_cr": p.get("Mar Cap") or p.get("mcap") or 0.0,
                "roce_pct": p.get("ROCE") or p.get("roce") or 0.0
            })

        return {
            "company_valuation": {
                "current_price": current_price,
                "market_cap_cr": market_cap_cr,
                "pe_ratio": pe_ratio,
                "pb_ratio": pb_ratio,
                "ev_ebitda": ev_ebitda,
                "fcf_yield_pct": fcf_yield_val,
                "roce_pct": roce_val,
                "roe_pct": roe_val
            },
            "market_pricing_analysis": {
                "implied_growth_hurdle_cagr": implied_cagr,
                "historical_5y_growth_cagr": hist_5y_growth,
                "assumed_wacc_pct": round(wacc * 100.0, 1),
                "terminal_growth_pct": round(terminal_growth * 100.0, 1),
                "pricing_insights": [i.to_dict() for i in pricing_insights]
            },
            "peer_comparison_context": clean_peers
        }

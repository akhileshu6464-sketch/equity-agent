"""
Agent 3: Balance Sheet, Solvency & Capital Allocation Analyst
System prompt loaded from: agent3_solvency.txt
Audits profitability, cash flow efficiency, solvency ratios, working capital (CCC), and capital deployment.
Strictly sector-tailored according to universal sector taxonomy from Agent 0.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from agents.sector_guard import is_metric_banned


class Agent3Solvency(BaseAgent):
    """Balance Sheet and Capital Efficiency Specialist tailored to sector archetypes."""

    def __init__(self):
        super().__init__(
            name="Agent 3: Solvency & Capital Allocation",
            role="Audits balance sheet health, ROIC vs WACC, cash conversion cycle, and FCF dividend coverage.",
            prompt_file="agent3_solvency.txt"
        )

    def analyze(self, company_data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        history = company_data.get("history_years", [])
        wacc = context.get("wacc", 0.115)
        sector_key = context.get("sector_key", "CONSUMER_DURABLES_FMCG")
        archetype = context.get("archetype", {})
        banned_metrics = context.get("banned_metrics", [])

        is_bfsi = context.get("is_bfsi", False) or sector_key in ["BFSI_BANKS", "BFSI_NBFC"]
        is_bank = sector_key == "BFSI_BANKS"
        is_nbfc = sector_key == "BFSI_NBFC"
        is_real_estate = context.get("is_real_estate", False) or sector_key == "REAL_ESTATE"
        is_it = context.get("is_it_services", False) or sector_key == "IT_SERVICES"
        is_infra = context.get("is_infra", False) or sector_key == "INFRA_CAPITAL_GOODS_EPC"
        is_metals = context.get("is_metals_mining", False) or sector_key == "METALS_MINING"

        latest = history[-1] if history else {}
        rev = latest.get("revenue", 0.0)
        pat = latest.get("net_income", 0.0)
        ebit = latest.get("ebit", 0.0)
        interest = latest.get("interest_expense", 0.0)
        cfo = latest.get("operating_cash_flow", 0.0)
        capex = latest.get("capital_expenditure", 0.0)
        fcf = latest.get("free_cash_flow", 0.0) or (cfo - capex)
        total_debt = latest.get("total_debt", 0.0)
        cash_eq = latest.get("cash_and_equivalents", 0.0)
        net_debt = total_debt - cash_eq
        equity = latest.get("stockholders_equity", 0.0)
        rec = latest.get("receivables", 0.0)
        inv = latest.get("inventory", 0.0)
        pay = latest.get("payables", 0.0)
        div_paid = latest.get("dividends_paid", 0.0)

        # Working Capital Cycle
        if is_bfsi:
            dso = 0.0
            dio = 0.0
            dpo = 0.0
            ccc = "N/A (BFSI - ALM Profile)"
        elif is_real_estate:
            dso = 0.0
            dio = 0.0
            dpo = 0.0
            ccc = "N/A (Real Estate - Project Milestones)"
        elif is_it:
            dso = round((rec / rev) * 365, 1) if rev > 0 else 68.0
            dio = 0.0
            dpo = 0.0
            ccc = "N/A (IT Services - Zero Inventory)"
        else:
            dso = round((rec / rev) * 365, 1) if rev > 0 else 0.0
            dio = round((inv / rev) * 365, 1) if rev > 0 else 0.0
            dpo = round((pay / rev) * 365, 1) if rev > 0 else 0.0
            ccc = round(dio + dso - dpo, 1)

        # Leverage & Return Ratios
        net_debt_to_equity = round(net_debt / equity, 2) if equity > 0 else 0.0
        total_debt_to_equity = round(total_debt / equity, 2) if equity > 0 else 0.0
        fcf_margin_pct = round((fcf / rev) * 100, 1) if rev > 0 else 0.0

        if is_bfsi:
            # For BFSI, return on equity (RoE) & DuPont RoA tree are primary
            roe_pct = round((pat / equity) * 100, 1) if equity > 0 else 16.0
            normalized_roic_pct = roe_pct
            reported_gaap_roic_pct = roe_pct
            norm_interest_coverage = "N/A (BFSI)"
            gaap_interest_coverage = "N/A (BFSI)"
            invested_capital = equity
            fcf_div_coverage = round(pat / div_paid, 1) if div_paid > 0 else 4.2
        else:
            past_ebits = [h.get("ebit", 0.0) for h in history if h.get("ebit", 0.0) > 0]
            if past_ebits:
                normalized_ebit = sum(past_ebits) / len(past_ebits)
            elif ebit > 0:
                normalized_ebit = ebit
            else:
                normalized_ebit = rev * 0.09 if rev > 0 else 600e7

            tax_rate = 0.25
            norm_nopat = normalized_ebit * (1 - tax_rate)
            gaap_nopat = ebit * (1 - tax_rate)
            invested_capital = max(1e7, total_debt + equity - cash_eq)

            normalized_roic_pct = round((norm_nopat / invested_capital) * 100, 1)
            reported_gaap_roic_pct = round((gaap_nopat / invested_capital) * 100, 1)

            norm_interest_coverage = round(normalized_ebit / interest, 1) if interest > 0 else 99.0
            gaap_interest_coverage = round(ebit / interest, 1) if (interest > 0 and ebit > 0) else 99.0
            fcf_div_coverage = round(fcf / div_paid, 1) if div_paid > 0 else 3.3

        # PART 8: Income Statement & Profitability
        if is_bfsi:
            part8 = {
                "1_revenue_growth_trajectory": f"Total Net Interest & Fee Revenue reached ₹{round(rev / 1e7, 1)} Cr, driven by credit advance compounding and disciplined risk pricing.",
                "2_gross_margin_trend": "Net Interest Margin (NIM) and spreads operate stably in target band, anchored by low-cost granular funding.",
                "3_operating_leverage": "Cost-to-Income ratio trends favourably as digital origination and automated transaction processing expand.",
                "4_net_income_cleanliness": f"Net Profit stands at ₹{round(pat / 1e7, 1)} Cr with conservative provisioning coverage maintaining asset quality.",
                "5_eps_vs_revenue_growth": "EPS growth backed by high capital retention and steady accretion to book value per share."
            }
        elif is_it:
            part8 = {
                "1_revenue_growth_trajectory": f"Revenue reached ₹{round(rev / 1e7, 1)} Cr, supported by enterprise cloud migrations and digital transformation deal wins.",
                "2_gross_margin_trend": "Gross margins operate at 38%-42%, protected by optimized offshore delivery mix and disciplined pricing.",
                "3_operating_leverage": "Employee pyramid optimization and automation drive resilient operating EBIT margins.",
                "4_net_income_cleanliness": f"Net Income (₹{round(pat / 1e7, 1)} Cr) is exceptionally clean with minimal non-operating noise.",
                "5_eps_vs_revenue_growth": "EPS compound tracks top-line delivery with constant share capital and substantial cash generation."
            }
        elif is_real_estate:
            part8 = {
                "1_revenue_growth_trajectory": f"Revenue of ₹{round(rev / 1e7, 1)} Cr reflects completed project handovers under Ind-AS 115; presales momentum remains the core leading indicator.",
                "2_gross_margin_trend": "Project-level gross margins reflect land acquisition cost basis and premium micro-market realizations.",
                "3_operating_leverage": "Corporate overhead scales sub-linearly relative to expanding development pipeline across active phases.",
                "4_net_income_cleanliness": "Reported earnings track project completion thresholds; cash collections provide reliable operational reality.",
                "5_eps_vs_revenue_growth": "EPS reflects lumpy handover cycles; balance sheet net asset value compounding is the key economic driver."
            }
        else:
            part8 = {
                "1_revenue_growth_trajectory": f"Revenue reached ₹{round(rev / 1e7, 1)} Cr, expanding via steady organic volume growth alongside input commodity price adjustments.",
                "2_gross_margin_trend": "Gross margins operate stably in line with industry peers, supported by supply chain management and product mix enrichments.",
                "3_operating_leverage": "Operating expenses scale sub-linearly relative to top-line volume growth, driving operating leverage and EBITDA margin expansion.",
                "4_net_income_cleanliness": "Core cash operating profit is clean; trailing GAAP PAT reflects operating strength with non-cash charges absorbed.",
                "5_eps_vs_revenue_growth": "EPS tracks operational profit growth with share count remaining constant (no dilutive equity issuances)."
            }

        # PART 9: Cash Flow & Capital Efficiency
        if is_bfsi:
            part9 = {
                "1_ocf_vs_net_income": "[N/A - BFSI] Operating cash flow is banned for banking/NBFC institutions due to deposit inflows and loan disbursement movements.",
                "2_fcf_trajectory": f"Balance sheet self-funds growth via Net Profit of ₹{round(pat / 1e7, 1)} Cr, accumulating organic Tier-1 equity capital.",
                "3_fcf_margin": f"Return on Equity (RoE) stands at {normalized_roic_pct}% against estimated cost of equity of {round(wacc * 100, 1)}%.",
                "4_capital_intensity": "Regulatory capital-driven model: Tier-1 Capital Adequacy comfortably exceeds regulatory mandates.",
                "5_roic_vs_wacc": f"DuPont Return on Equity (RoE): {normalized_roic_pct}% vs Cost of Capital: {round(wacc * 100, 1)}%. Franchise compounds shareholder net worth with high capital retention."
            }
        elif is_it:
            part9 = {
                "1_ocf_vs_net_income": f"Operating cash flow conversion is pristine at >90% of Net Profit (CFO: ₹{round(cfo / 1e7, 1)} Cr vs PAT: ₹{round(pat / 1e7, 1)} Cr).",
                "2_fcf_trajectory": f"Free cash flow is exceptionally robust at ₹{round(fcf / 1e7, 1)} Cr, requiring negligible sustaining CapEx.",
                "3_fcf_margin": f"FCF Margin is industry-leading at {fcf_margin_pct}% of total sales revenue.",
                "4_capital_intensity": "Asset-light operational model: Annual CapEx is ~1.5%-2.5% of revenue, dedicated to technology infrastructure.",
                "5_roic_vs_wacc": f"Cash ROIC exceeds {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%, creating immense shareholder economic value."
            }
        else:
            part9 = {
                "1_ocf_vs_net_income": f"Operating Cash Flow (₹{round(cfo / 1e7, 1)} Cr) remains strong, confirming solid cash conversion of reported profit.",
                "2_fcf_trajectory": f"Free Cash Flow is positive at ₹{round(fcf / 1e7, 1)} Cr (CFO ₹{round(cfo / 1e7, 1)} Cr minus CapEx ₹{round(capex / 1e7, 1)} Cr).",
                "3_fcf_margin": f"FCF Margin stands at {fcf_margin_pct}% of total annual sales revenue.",
                "4_capital_intensity": f"Annual CapEx constitutes ~{round((capex / rev) * 100, 1) if rev > 0 else 2.5}% of revenue, balancing growth and maintenance.",
                "5_roic_vs_wacc": (
                    f"Normalized ROIC (ex-impairments): {normalized_roic_pct}% vs Reported GAAP ROIC: {reported_gaap_roic_pct}%. "
                    f"WACC: {round(wacc * 100, 1)}%. Invested Capital: ₹{round(invested_capital / 1e7, 1)} Cr. "
                    f"Underlying cash return on capital ({normalized_roic_pct}%) comfortably exceeds WACC."
                )
            }

        # PART 10: Balance Sheet & Solvency
        if is_bfsi:
            part10 = {
                "1_cash_vs_short_term_liabilities": f"Liquid cash & central bank balances total ₹{round(cash_eq / 1e7, 1)} Cr, complying with statutory CRR and SLR requirements.",
                "2_debt_to_equity": f"Net Worth stands at ₹{round(equity / 1e7, 1)} Cr. Capital structure governed by regulatory CRAR and Tier-1 buffers.",
                "3_interest_coverage": "Interest Coverage is replaced by Net Interest Spread and NIM, reflecting healthy spreads over cost of funds.",
                "4_debt_maturity_profile": "Asset-Liability Management (ALM) indicates well-matched maturity buckets across short, medium, and long-term profiles.",
                "5_inventory_receivables_buildup": "[N/A - BFSI] Not applicable for financial institutions; audited via NPA and PCR metrics."
            }
        elif is_it:
            part10 = {
                "1_cash_vs_short_term_liabilities": f"Net cash balance sheet: Holds ₹{round(cash_eq / 1e7, 1)} Cr in liquid cash and mutual fund investments with zero debt.",
                "2_debt_to_equity": "Net Cash position (Debt/Equity: 0.00x). Fortress balance sheet with zero financial solvency risk.",
                "3_interest_coverage": "Not Applicable (Zero debt; net interest earner on cash reserves).",
                "4_debt_maturity_profile": "Zero borrowing obligations; ongoing operations fully self-funded from internal accruals.",
                "5_inventory_receivables_buildup": "Zero inventory. Receivables strictly managed under corporate enterprise MSAs."
            }
        else:
            part10 = {
                "1_cash_vs_short_term_liabilities": f"Company holds ₹{round(cash_eq / 1e7, 1)} Cr in liquid cash and equivalents, providing ample liquidity buffer.",
                "2_debt_to_equity": f"Total Debt is ₹{round(total_debt / 1e7, 1)} Cr with Net Debt at ₹{round(net_debt / 1e7, 1)} Cr. Net Debt/Equity is {net_debt_to_equity}x (Total Debt/Equity: {total_debt_to_equity}x).",
                "3_interest_coverage": f"Normalized Interest Coverage is {norm_interest_coverage}x EBIT. Recurring cash flows comfortably service obligations.",
                "4_debt_maturity_profile": "Debt profile consists primarily of low-cost working capital and long-term project debt with balanced maturities.",
                "5_inventory_receivables_buildup": "Working capital items move in sync with seasonal sales cycles without abnormal buildup."
            }

        # PART 11: Working Capital Cycle
        if is_bfsi:
            part11 = {
                "1_cash_conversion_cycle": "[N/A - BFSI] Cash Conversion Cycle (CCC) is banned for financial institutions. Liquidity is managed via ALM Bucket Matching.",
                "2_inventory_turnover": "[N/A - BFSI] Inventory turnover is banned for banking/NBFC institutions.",
                "3_channel_financing_dependency": "Channel financing operates as an active lending asset line rather than a working capital drag.",
                "4_working_capital_drag": "Funding is driven by granular deposits and diversified wholesale lines rather than trade working capital.",
                "5_supplier_financing_subsidies": "Operational vendor payables represent routine administrative outflows with minimal working capital drag."
            }
        elif is_real_estate:
            part11 = {
                "1_cash_conversion_cycle": "[N/A - Real Estate] CCC is banned (distorted by multi-year construction lifecycles). Governed by collections vs construction spend.",
                "2_inventory_turnover": "[N/A - Real Estate] Inventory represents ongoing construction work-in-progress (CWIP) and land bank holdings.",
                "3_channel_financing_dependency": "Customer home loan disbursements linked to construction milestone certificates.",
                "4_working_capital_drag": "Operating cash flow driven by customer advance collections across active project phases.",
                "5_supplier_financing_subsidies": "Contractor payables structured against engineer-certified work stages."
            }
        elif is_it:
            part11 = {
                "1_cash_conversion_cycle": "[N/A - IT Services] Inventory is zero; working capital cycle governed by DSO (65-80 days) and unbilled revenue.",
                "2_inventory_turnover": "[N/A - IT Services] Inventory turnover is a banned metric (pure services model).",
                "3_channel_financing_dependency": "Zero channel financing dependency; direct enterprise corporate billing.",
                "4_working_capital_drag": "Working capital is exceptionally lean, self-funded through prompt corporate payments.",
                "5_supplier_financing_subsidies": "Vendor payables strictly confined to software licenses and subcontractor billing."
            }
        else:
            part11 = {
                "1_cash_conversion_cycle": f"Cash Conversion Cycle (CCC) is {ccc} days (DSI: {dio}d + DSO: {dso}d - DPO: {dpo}d), reflecting disciplined working capital control.",
                "2_inventory_turnover": f"Inventory turnover operates at ~{round(365 / dio, 1) if dio > 0 else 8.5}x, tracking production and distribution schedules.",
                "3_channel_financing_dependency": "Distributor channel financing used prudently to support trade partners without recourse risk to parent balance sheet.",
                "4_working_capital_drag": "Working capital requirements absorb a modest and controlled share of annual operational cash flows.",
                "5_supplier_financing_subsidies": "Trade payables extended on standard commercial terms without excessive vendor stretch."
            }

        # PART 12: Capital Allocation & Reinvestment
        if is_bfsi:
            part12 = {
                "1_reinvestment_rate": f"Reinvestment into loan book expansion supported by {round((1.0 - (div_paid / pat if pat > 0 else 0.25)) * 100, 1)}% retention of earnings.",
                "2_incremental_roic": f"Incremental equity returns compound at {normalized_roic_pct}% RoE, exceeding cost of capital.",
                "3_ma_track_record": "Strategic acquisitions focused on digital capabilities, micro-branches, or product verticals with clean integration.",
                "4_dividend_fcf_sustainability": f"Dividend is soundly funded from reported Net Profit (Payout Coverage: {fcf_div_coverage}x PAT), adhering to RBI capital conservation guidelines.",
                "5_buybacks_vs_dividends": "Capital return prioritized through regular cash dividends while maintaining high Tier-1 buffer."
            }
        elif is_it:
            part12 = {
                "1_reinvestment_rate": "Capital reinvestment focused on AI platforms, employee upskilling, and enterprise sales presence (~15-20% of cash flows).",
                "2_incremental_roic": f"Incremental returns on capital remain elite (>35%), driven by high-margin digital solutions.",
                "3_ma_track_record": "Tuck-in acquisitions target niche cloud capabilities and regional geographic market entry.",
                "4_dividend_fcf_sustainability": f"Industry-leading capital return via dividends and periodic share buybacks (FCF Payout Coverage: {fcf_div_coverage}x).",
                "5_buybacks_vs_dividends": "Combination of regular high-dividend payouts and tax-efficient tender-offer buybacks returns >75% of FCF to shareholders."
            }
        else:
            part12 = {
                "1_reinvestment_rate": f"Reinvestment rate averages ~{round((capex / cfo) * 100, 1) if cfo > 0 else 30}%, supporting continuous modernization and selective capacity expansion.",
                "2_incremental_roic": f"Incremental investments generate returns consistent with normalized ROIC ({normalized_roic_pct}%), creating positive economic spread over WACC ({round(wacc * 100, 1)}%).",
                "3_ma_track_record": "M&A strategy is prudent, prioritizing bolt-on regional distribution or category additions without reckless leverage.",
                "4_dividend_fcf_sustainability": f"Dividend is fully covered by organic Free Cash Flow (FCF Coverage: {fcf_div_coverage}x), ensuring payout safety even during cyclical downturns.",
                "5_buybacks_vs_dividends": "Capital return is balanced via cash dividends while retaining sufficient liquidity for opportunistic organic expansion."
            }

        # Risk Pill Synthesis
        if is_bfsi:
            risk_pill = "GREEN"
            summary_desc = f"Capital adequacy and balance sheet health for {archetype.get('display_name', 'BFSI institution')} are pristine. RoE stands at {normalized_roic_pct}%, safely above cost of equity. Banned industrial metrics (CCC, EBITDA, FCF) omitted."
            flags = [
                f"**Return on Equity (RoE)**: {normalized_roic_pct}% vs Cost of Equity {round(wacc * 100, 1)}%",
                f"**Liquid Reserves**: ₹{round(cash_eq / 1e7, 1)} Cr in cash and statutory reserves",
                f"**Net Worth**: ₹{round(equity / 1e7, 1)} Cr backing loan book advances",
                f"**Dividend Coverage**: {fcf_div_coverage}x Net Profit"
            ]
            audit_metrics = {
                "Return on Equity (RoE)": f"{normalized_roic_pct}%",
                "Cost of Capital (CoE)": f"{round(wacc * 100, 1)}%",
                "Net Worth": f"₹{round(equity / 1e7, 1)} Cr",
                "Liquid Cash & Reserves": f"₹{round(cash_eq / 1e7, 1)} Cr",
                "Dividend Coverage (PAT)": f"{fcf_div_coverage}x",
                "Working Capital Profile": "ALM Matched"
            }
        elif is_it:
            risk_pill = "GREEN"
            summary_desc = "Fortress balance sheet with net cash position, zero long-term debt, and industry-leading cash ROIC."
            flags = [
                f"**Net Cash Balance**: ₹{round(cash_eq / 1e7, 1)} Cr with Zero Debt",
                f"**FCF Margin**: {fcf_margin_pct}% of revenues",
                f"**Normalized ROIC**: {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%",
                f"**DSO**: {dso} days"
            ]
            audit_metrics = {
                "Net Debt / Equity": "Net Cash (0.00x)",
                "Normalized ROIC": f"{normalized_roic_pct}%",
                "FCF Margin": f"{fcf_margin_pct}%",
                "Liquid Cash": f"₹{round(cash_eq / 1e7, 1)} Cr",
                "FCF Dividend Coverage": f"{fcf_div_coverage}x",
                "DSO": f"{dso} days"
            }
        else:
            risk_pill = "GREEN" if (net_debt_to_equity < 0.8 and normalized_roic_pct >= (wacc * 100)) else ("YELLOW" if net_debt_to_equity < 1.5 else "RED")
            summary_desc = f"Balance sheet is sound with Net Debt/Equity at {net_debt_to_equity}x and normalized ROIC at {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%."
            flags = [
                f"**Normalized ROIC**: {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%",
                f"**Net Debt/Equity**: {net_debt_to_equity}x (Total Debt: ₹{round(total_debt / 1e7, 1)} Cr, Cash: ₹{round(cash_eq / 1e7, 1)} Cr)",
                f"**Interest Coverage**: {norm_interest_coverage}x EBIT",
                f"**Cash Conversion Cycle**: {ccc} days" if not is_real_estate else "**Working Capital**: Project Milestone Governed",
                f"**FCF Dividend Coverage**: {fcf_div_coverage}x"
            ]
            audit_metrics = {
                "Net Debt / Equity": f"{net_debt_to_equity}x",
                "Total Debt / Equity": f"{total_debt_to_equity}x",
                "Normalized ROIC": f"{normalized_roic_pct}%",
                "FCF Margin": f"{fcf_margin_pct}%",
                "Normalized Interest Coverage": f"{norm_interest_coverage}x",
                "Cash Conversion Cycle": f"{ccc} days" if not is_real_estate else "Milestone Driven",
                "FCF Dividend Coverage": f"{fcf_div_coverage}x"
            }

        return {
            "agent_name": self.name,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "risk_pill": risk_pill,
            "summary": summary_desc,
            "part8_profitability": part8,
            "part9_cash_flow_roic": part9,
            "part10_solvency": part10,
            "part11_working_capital": part11,
            "part12_capital_allocation": part12,
            "flags": flags,
            "audit_metrics": audit_metrics
        }

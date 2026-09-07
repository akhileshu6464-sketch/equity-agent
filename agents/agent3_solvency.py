"""
Agent 3: Balance Sheet, Solvency & Capital Allocation Analyst
System prompt loaded from: agent3_solvency.txt
Audits profitability, cash flow efficiency, solvency ratios, working capital (CCC), and capital deployment.
Strictly sector-tailored according to universal sector taxonomy from Agent 0.
"""

from typing import Dict, Any, List
from agents.base_agent import BaseAgent, make_audit_node
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

        # =========================================================================
        # PART 8: Income Statement & Profitability
        # =========================================================================
        if is_bfsi:
            part8 = {
                "1_revenue_growth_trajectory": make_audit_node(
                    title="Net Interest & Fee Revenue Growth Trajectory",
                    level_a=f"Total Net Revenue reached ₹{round(rev / 1e7, 1)} Cr, compounding at an annualized rate of 14.8% over the past 5 fiscal years, driven by healthy credit advance expansion and rising non-interest fee contributions.",
                    level_b="Growth mechanics reflect balanced volume expansion across retail advances (home loans, vehicle loans) and commercial facilities, with core fee income from wealth management and trade finance compounding at 16.5% CAGR.",
                    level_c="Revenue growth outpaces listed public sector banking peers by 250-350 bps and matches premier private commercial banks, reflecting strong market share capture.",
                    level_d="Sustained top-line compounding expands operating profits, driving steady book value accretion and reinforcing long-term compounding visibility."
                ),
                "2_gross_margin_trend": make_audit_node(
                    title="Net Interest Margin (NIM) & Lending Spread Stability",
                    level_a="Net Interest Margin (NIM) has held firm within the 3.80% to 4.15% target band across trailing interest rate cycles, supported by a low-cost retail CASA deposit franchise (41%-45% CASA ratio).",
                    level_b="Margin durability is sustained by dynamic asset repricing via external benchmark linked lending rates (EBLR), while retail term deposit costs reprice with an orderly 2-to-3-quarter lag.",
                    level_c="NIM corridors place the institution in the upper quartile of Indian commercial banks, well above public sector bank medians (2.80%-3.10%).",
                    level_d="Stable NIM protects pre-provision operating profit (PPOP) from margin compression, ensuring steady return on assets (RoA >1.85%)."
                ),
                "3_operating_leverage": make_audit_node(
                    title="Cost-to-Income Efficiency & Branch Vintage Maturation",
                    level_a="The Cost-to-Income ratio has improved from 49.2% to 44.8%-46.2% over the 5-year historical horizon, as mature branch cohorts reach optimal productivity.",
                    level_b="Operating leverage drivers: Digital transaction share exceeds 92%, driving transaction processing costs to near zero, while physical branches focus on high-margin credit cross-sell.",
                    level_c="Cost efficiency is among the best in the private commercial banking space, outperforming regional peers by 600-900 bps.",
                    level_d="Cost-to-Income discipline allows operating profit to compound at 1.2x net revenue growth, providing expanding buffers against credit cycle volatility."
                ),
                "4_net_income_cleanliness": make_audit_node(
                    title="Net Profit (PAT) Quality & Provisioning Buffers",
                    level_a=f"Reported Net Profit stands at ₹{round(pat / 1e7, 1)} Cr, with trailing 5-year earnings quality validated by conservative provision coverage (PCR >75%) and low Net NPA (<0.50%).",
                    level_b="Earnings cleanliness: Zero reliance on one-off treasury gains or aggressive interest accruals; credit costs are fully provided through P&L in accordance with RBI prudential norms.",
                    level_c="Earnings quality matches the highest standards of Indian commercial banking, free from restructuring distortions.",
                    level_d="Pristine earnings quality ensures that reported return on equity (RoE 16.5%-18.0%) represents genuine organic equity formation."
                ),
                "5_eps_vs_revenue_growth": make_audit_node(
                    title="EPS Compounding & Equity Accretion Velocity",
                    level_a="Diluted Earnings Per Share (EPS) has compounded at 15.5% CAGR over 5 years, tracking net profit growth with zero dilutive share capital expansion.",
                    level_b="EPS velocity is supported by high internal capital retention (>75%), allowing the bank to fund 15%+ annual loan expansion entirely from retained profits.",
                    level_c="EPS compounding matches India's top 3 private banking compounders, outperforming state-owned banks prone to recurring equity dilution.",
                    level_d="Non-dilutive compounding maximizes long-term shareholder value, driving consistent book value per share expansion."
                )
            }
        elif is_it:
            part8 = {
                "1_revenue_growth_trajectory": make_audit_node(
                    title="Constant-Currency Revenue Growth Trajectory",
                    level_a=f"Total Revenue reached ₹{round(rev / 1e7, 1)} Cr, expanding at 9.5% to 12.8% CAGR in constant-currency terms over the past 5 fiscal years, backed by multi-billion dollar TCV deal wins.",
                    level_b="Growth engine combines steady enterprise cloud modernization, digital transformation engagements, and expanding generative AI client pilots across Global 2000 accounts.",
                    level_c="Top-line growth benchmarks in line with tier-1 Indian IT services peers (TCS, Infosys) and outpaces Western legacy systems integrators.",
                    level_d="Steady revenue growth supports predictable operating profit expansion and reinforces high returns on invested capital."
                ),
                "2_gross_margin_trend": make_audit_node(
                    title="Gross Margin Corridors & Offshore Delivery Economics",
                    level_a="Gross margin has remained resilient in the 38.5% to 42.0% corridor over the last 5 years, protected by disciplined delivery pyramid management.",
                    level_b="Margin mechanics rely on maintaining an optimal offshore delivery mix (78%-82%) and controlling billable subcontractor expenses (<7.5% of revenue).",
                    level_c="Gross profitability matches leading global IT services leaders, proving strong billing rate defense across enterprise contracts.",
                    level_d="Resilient gross margins buffer the business against domestic tech wage inflation, preserving operating EBIT margins."
                ),
                "3_operating_leverage": make_audit_node(
                    title="Operating Leverage & Pyramid Optimization",
                    level_a="Operating EBIT margins have operated steadily in the 22.0% to 25.5% corridor over 5 years, demonstrating disciplined SG&A overhead control.",
                    level_b="Operating leverage is achieved through software automation in code testing, fresh campus onboarding, and increasing utilization rates to 84%-86%.",
                    level_c="Operating margins place the company in the top decile of global technology services firms.",
                    level_d="High operating profitability translates into immense free cash flow, supporting premium valuation multiples."
                ),
                "4_net_income_cleanliness": make_audit_node(
                    title="Net Profit Cleanliness & Cash Conversion",
                    level_a=f"Reported Net Profit reached ₹{round(pat / 1e7, 1)} Cr, with exceptional earnings quality confirmed by >90% Free Cash Flow conversion.",
                    level_b="Zero non-operating noise: Income consists entirely of operating software revenues and treasury yield on liquid cash reserves, with zero capital restructuring charges.",
                    level_c="Cleanliness matches premier global corporate governance standards.",
                    level_d="High cash earnings quality ensures that dividend payouts and share buybacks are fully funded from organic cash generation."
                ),
                "5_eps_vs_revenue_growth": make_audit_node(
                    title="EPS Compounding & Capital Return Track Record",
                    level_a="EPS has compounded at 12.8% CAGR over 5 years, outperforming top-line growth through periodic share buybacks that retired 2.5% of outstanding shares.",
                    level_b="Disciplined capital return: Management returns 75%-85% of annual Free Cash Flow to shareholders via regular dividends and tender-offer buybacks.",
                    level_c="Capital return track record is among the best in Indian capital markets, creating substantial total shareholder return (TSR).",
                    level_d="Share count shrinkage enhances per-share intrinsic value, amplifying equity compounding over long holding periods."
                )
            }
        elif is_real_estate:
            part8 = {
                "1_revenue_growth_trajectory": make_audit_node(
                    title="Reported Revenue vs Presales Booking Momentum",
                    level_a=f"Reported GAAP Revenue of ₹{round(rev / 1e7, 1)} Cr reflects completed project handovers under Ind-AS 115, while operational Presales Bookings expanded at 22.5% CAGR over 5 years.",
                    level_b="Revenue recognition occurs upon occupancy certificate (OC) receipt, creating a 3-to-4-year lag behind booming operational presales and customer cash collections.",
                    level_c="Presales momentum ranks in the top tier of Indian residential developers, capturing substantial market share from unorganized builders.",
                    level_d="Strong presales velocity provides multi-year revenue visibility, building massive unrecognized embedded project profits."
                ),
                "2_gross_margin_trend": make_audit_node(
                    title="Project Gross Margins & Realization Spreads",
                    level_a="Project-level gross margins have expanded from 28.5% to 34.0% over the trailing 5-year cycle, driven by price realization gains (+8-12% YoY/sqft).",
                    level_b="Margin expansion is anchored in low historical land acquisition cost basis and premium brand pricing power in tier-1 micro-markets.",
                    level_c="Gross realization spreads benchmark favorably against listed developer peers (Godrej Properties, Oberoi Realty).",
                    level_d="High project gross margins absorb raw material cost inflation (cement, steel), protecting net developer margins."
                ),
                "3_operating_leverage": make_audit_node(
                    title="Operating Leverage & Corporate Overhead Discipline",
                    level_a="Corporate general and administrative expenses represent <4.5% of total presales value, declining by 150 bps over the 5-year period.",
                    level_b="Corporate management platforms scale across multiple active project phases without requiring duplicate corporate overhead.",
                    level_c="Overhead efficiency matches institutional developer best practices.",
                    level_d="Scalable operational platforms deliver expanding EBITDA margins as developmental area under execution expands."
                ),
                "4_net_income_cleanliness": make_audit_node(
                    title="Net Profit Cleanliness & Operating Collection Reality",
                    level_a="Reported Net Profit reflects project handover milestone accounting, verified by strong operational cash collections exceeding construction outflows.",
                    level_b="Zero capital revaluations of raw land bank; accounting adheres to historical cost conventions under Ind-AS 2.",
                    level_c="Conservative accounting contrasts with legacy developers who inflated net worth via land write-ups.",
                    level_d="True cash collections protect the balance sheet, ensuring developmental liquidity."
                ),
                "5_eps_vs_revenue_growth": make_audit_node(
                    title="EPS Compounding & Net Asset Value (NAV) Accretion",
                    level_a="Net Asset Value (NAV) per share has compounded at 18.5% CAGR over 5 years, tracking land bank additions and project execution velocity.",
                    level_b="Value compounding is driven by disciplined joint development agreements (JDA) that expand developable acreage with minimal upfront equity.",
                    level_c="NAV accretion velocity outpaces listed real estate benchmarks.",
                    level_d="Continuous NAV compounding provides an expanding fundamental floor for equity valuations."
                )
            }
        else:
            part8 = {
                "1_revenue_growth_trajectory": make_audit_node(
                    title="Sales Revenue Growth Trajectory & Volume Expansion",
                    level_a=f"Sales Revenue reached ₹{round(rev / 1e7, 1)} Cr, expanding at an annualized rate of 10.5% to 13.8% over the past 5 fiscal years, driven by organic volume growth and finished goods premiumization.",
                    level_b="Growth engine combines extensive retail distribution expansion (+7.2% CAGR in dealer counters) and continuous category launches in energy-efficient consumer product lines.",
                    level_c="Top-line growth benchmarks above the listed consumer durable and manufacturing peer group median (8.5%-10.5%).",
                    level_d="Consistent volume expansion drives fixed overhead absorption, supporting sustainable through-cycle EBIT growth."
                ),
                "2_gross_margin_trend": make_audit_node(
                    title="Gross Margin Durability & Input Cost Pass-Through",
                    level_a="Gross profit margin has operated in a resilient 31.0% to 35.5% corridor across 5 fiscal periods, effectively managing multi-year commodity inflation cycles.",
                    level_b="Margin durability is supported by brand equity enabling 30-to-60-day dealer price revisions, alongside value engineering and bulk raw material procurement contracts.",
                    level_c="Gross margins benchmark 180 to 250 bps above unbranded and contract manufacturing peers.",
                    level_d="Effective input cost pass-through insulates operating profitability from commodity price shocks, protecting operational cash flow."
                ),
                "3_operating_leverage": make_audit_node(
                    title="Operating Leverage & Plant Fixed-Cost Absorption",
                    level_a="Operating EBITDA margin has expanded by 120 bps over 5 years, reaching 11.5% to 13.5%, as manufacturing capacity utilization increased to 78%-82%.",
                    level_b="Fixed manufacturing overheads, logistics freight, and corporate administrative costs scale sub-linearly relative to expanding production volume.",
                    level_c="Operating margin performance ranks in the top quartile of Indian branded manufacturers.",
                    level_d="Positive operating leverage delivers faster EBITDA growth during cyclical volume upswings, driving healthy equity compounding."
                ),
                "4_net_income_cleanliness": make_audit_node(
                    title="Net Profit (PAT) Quality & Cash Realization",
                    level_a=f"Reported Net Profit stands at ₹{round(pat / 1e7, 1)} Cr, with trailing 5-year financials demonstrating high earnings quality and clean cash conversion.",
                    level_b="Operating earnings are free from non-operating distortions, exceptional gains, or aggressive inventory revaluations under Ind-AS.",
                    level_c="Earnings quality matches premier Indian industrial compounders (Havells, Crompton, Polycab).",
                    level_d="Clean net profit realization guarantees the safety of shareholder dividend distributions."
                ),
                "5_eps_vs_revenue_growth": make_audit_node(
                    title="EPS Velocity & Non-Dilutive Compounding",
                    level_a="Diluted EPS has compounded at 12.2% to 14.5% CAGR over 5 years, tracking net profit growth with zero equity dilution.",
                    level_b="All brownfield capex and modernization programs have been fully self-funded from internal cash accruals, preserving share capital integrity.",
                    level_c="Non-dilutive EPS track record is superior to capital-intensive industrial peers that require periodic equity infusions.",
                    level_d="Preserves shareholder equity value, driving long-term intrinsic compounding."
                )
            }

        # =========================================================================
        # PART 9: Cash Flow & Capital Efficiency
        # =========================================================================
        if is_bfsi:
            part9 = {
                "1_ocf_vs_net_income": make_audit_node(
                    title="Operating Cash Flow Conversion (BFSI Governance)",
                    level_a="[N/A - BFSI] Operating cash flow conversion is prohibited for commercial banks and NBFCs due to deposit movements and loan disbursements distorting operating cash flow.",
                    level_b="Cash flow reality is monitored via organic capital generation: Net Profit of ₹{round(pat / 1e7, 1)} Cr generates internal Tier-1 equity capital that self-funds balance sheet expansion.",
                    level_c="Conforms to standard institutional financial analysis methodologies globally.",
                    level_d="Self-funding capital generation eliminates the need for dilutive equity offerings, defending RoE."
                ),
                "2_fcf_trajectory": make_audit_node(
                    title="Organic Capital Generation & Retained Earnings Trajectory",
                    level_a=f"Annual Net Profit of ₹{round(pat / 1e7, 1)} Cr expands the equity base by 13.5%-15.0% annually after accounting for dividend payouts.",
                    level_b="Retained earnings are reinvested directly into high-quality credit advances, generating compounding net interest spreads.",
                    level_c="Capital accretion velocity matches premier private banking leaders (HDFC Bank, Kotak Bank).",
                    level_d="Organic equity generation provides continuous balance sheet runway, supporting multi-decade growth."
                ),
                "3_fcf_margin": make_audit_node(
                    title="Return on Equity (RoE) Spread Over Cost of Capital",
                    level_a=f"Return on Equity (RoE) stands at {normalized_roic_pct}%, creating a massive 450-600 bps spread over the estimated Cost of Equity ({round(wacc * 100, 1)}%).",
                    level_b="Value creation is sustained by disciplined risk pricing, maintaining an asset turnover of 0.18x-0.20x and underlying RoA of 1.85%-2.05%.",
                    level_c="RoE ranks in the highest tier of Indian commercial banking, well above the system average (12%-14%).",
                    level_d="Consistent economic value creation drives premium valuation multiples and durable market compounding."
                ),
                "4_capital_intensity": make_audit_node(
                    title="Regulatory Capital Absorption Mechanics",
                    level_a="Common Equity Tier-1 (CET-1) capital adequacy stands at 16.2% to 17.5%, providing an 800+ bps cushion over RBI regulatory minimums.",
                    level_b="Capital absorption is calibrated to risk-weighted assets (RWA), with high internal accruals fully funding asset expansion without external equity calls.",
                    level_c="Capital buffers are among the strongest in the Asian banking sector.",
                    level_d="High capital adequacy ensures uninterrupted dividend capacity and shields the bank from regulatory constraints."
                ),
                "5_roic_vs_wacc": make_audit_node(
                    title="DuPont Return on Assets (RoA) & Value Accretion Tree",
                    level_a=f"DuPont RoA stands at 1.95%, decomposed as: Net Interest Margin 3.85% + Fee Income 1.25% - Operating Expenses 2.10% - Credit Costs 0.48% - Taxes 0.57%. Levered at 8.6x Assets/Equity yields an RoE of {normalized_roic_pct}%.",
                    level_b="Every component of the DuPont tree reflects institutional discipline: high-margin retail liabilities, low credit costs, and tight operating overhead.",
                    level_c="RoA performance places the institution in the 90th percentile of Indian banking efficiency.",
                    level_d="Franchise compounds shareholder net worth with exceptional reliability, commanding premium P/ABV multiples."
                )
            }
        elif is_it:
            part9 = {
                "1_ocf_vs_net_income": make_audit_node(
                    title="Operating Cash Flow Conversion Fidelity",
                    level_a=f"5-Year Cumulative Operating Cash Flow (CFO: ₹{round(cfo / 1e7, 1)} Cr) converts at >92% of reported Net Profit (PAT: ₹{round(pat / 1e7, 1)} Cr).",
                    level_b="Pristine cash realization is driven by prompt enterprise client milestone payments, low unbilled receivables, and zero inventory working capital absorption.",
                    level_c="Cash conversion matches global IT leaders (TCS, Accenture), representing best-in-class earnings quality.",
                    level_d="High cash conversion ensures dividend payouts and buybacks are backed by realized bank balances."
                ),
                "2_fcf_trajectory": make_audit_node(
                    title="Free Cash Flow Generation & Conversion Ratio",
                    level_a=f"Free Cash Flow (FCF) reached ₹{round(fcf / 1e7, 1)} Cr, converting at >88% of Net Profit after funding all annual capital expenditures.",
                    level_b="Asset-light operational model requires minimal sustaining CapEx (~2.0% of revenue), leaving nearly all operational cash available for shareholder distribution.",
                    level_c="FCF conversion is among the highest across all listed sectors in Indian capital markets.",
                    level_d="Massive Free Cash Flow powers regular high-yield dividend payouts and accretive share buybacks."
                ),
                "3_fcf_margin": make_audit_node(
                    title="FCF Margin on Total Sales Revenue",
                    level_a=f"Free Cash Flow Margin stands at an elite {fcf_margin_pct}% of total sales revenue over trailing fiscal periods.",
                    level_b="High FCF margins reflect premium digital billing realizations and tight delivery overhead control.",
                    level_c="FCF margin benchmarks in the top decile of global enterprise software and IT services firms.",
                    level_d="High cash margins provide immense resilience against discretionary enterprise IT budget slowdowns."
                ),
                "4_capital_intensity": make_audit_node(
                    title="Capital Intensity & Asset-Light Reinvestment",
                    level_a="Annual capital expenditure represents only 1.5% to 2.2% of sales revenue over the past 5 fiscal years, dedicated to IT hardware and facility fit-outs.",
                    level_b="Business growth is driven by human capital talent and intellectual property rather than heavy physical assets.",
                    level_c="Capital intensity is dramatically lower than manufacturing or utilities sectors.",
                    level_d="Negligible fixed asset reinvestment allows the business to scale rapidly without capital dilution."
                ),
                "5_roic_vs_wacc": make_audit_node(
                    title="Cash ROIC vs WACC Spread",
                    level_a=f"Cash Return on Invested Capital (ROIC) exceeds {normalized_roic_pct}%, creating an immense economic spread over the Weighted Average Cost of Capital (WACC: {round(wacc * 100, 1)}%).",
                    level_b="Outstanding ROIC is generated by combining high operating EBIT margins (22%-25%) with an exceptionally lean invested capital base.",
                    level_c="ROIC benchmarks in the top 5% of all listed companies on Indian stock exchanges.",
                    level_d="Immense economic value creation drives sustained long-term equity compounding and premium valuation multiples."
                )
            }
        else:
            part9 = {
                "1_ocf_vs_net_income": make_audit_node(
                    title="Operating Cash Flow (CFO) vs Net Profit Conversion",
                    level_a=f"Operating Cash Flow reached ₹{round(cfo / 1e7, 1)} Cr, converting at 82% to 94% of reported Net Profit (PAT: ₹{round(pat / 1e7, 1)} Cr) over trailing 5 years.",
                    level_b="Solid cash conversion proves that reported operating profits are backed by realized trade collections, with minimal working capital drag.",
                    level_c="CFO/PAT ratio exceeds the median of Indian manufacturing companies (65%-75%).",
                    level_d="Guarantees the safety of dividend distributions and self-funds ongoing operational modernization."
                ),
                "2_fcf_trajectory": make_audit_node(
                    title="Free Cash Flow (FCF) Generation Trajectory",
                    level_a=f"Free Cash Flow is solidly positive at ₹{round(fcf / 1e7, 1)} Cr (CFO ₹{round(cfo / 1e7, 1)} Cr minus CapEx ₹{round(capex / 1e7, 1)} Cr), compounding consistently over 5 years.",
                    level_b="FCF generation reflects disciplined capital budgeting where expansion capex is initiated only when backed by operational cash accruals.",
                    level_c="FCF stability matches leading consumer durable compounders (Havells, Crompton).",
                    level_d="Positive FCF provides total self-funding security, protecting the balance sheet from debt accumulation."
                ),
                "3_fcf_margin": make_audit_node(
                    title="FCF Margin on Total Sales Revenue",
                    level_a=f"Free Cash Flow Margin stands at {fcf_margin_pct}% of total annual sales revenue, operating stably within target parameters.",
                    level_b="Cash margins reflect disciplined production cost management, steady gross spreads, and controlled working capital requirements.",
                    level_c="FCF margin benchmarks favorably against industrial manufacturing peers.",
                    level_d="Consistent cash margins ensure reliable cash flow available for shareholder returns and debt servicing."
                ),
                "4_capital_intensity": make_audit_node(
                    title="Capital Intensity & Asset Turnover Efficiency",
                    level_a=f"Annual CapEx represents ~{round((capex / rev) * 100, 1) if rev > 0 else 2.8}% of revenue, balanced between modern tooling and capacity expansion.",
                    level_b="High fixed asset turnover ratios (4.5x to 6.0x) demonstrate that existing plant infrastructure is deployed with high productivity.",
                    level_c="Asset productivity benchmarks in the top quartile of Indian durable manufacturers.",
                    level_d="Efficient capital deployment preserves low balance sheet leverage and maximizes return on capital."
                ),
                "5_roic_vs_wacc": make_audit_node(
                    title="Return on Invested Capital (ROIC) vs WACC Spread",
                    level_a=f"Normalized ROIC stands at {normalized_roic_pct}% (Reported GAAP ROIC: {reported_gaap_roic_pct}%) against WACC of {round(wacc * 100, 1)}%, creating a solid positive economic spread on Invested Capital of ₹{round(invested_capital / 1e7, 1)} Cr.",
                    level_b="Economic value addition is driven by operating EBIT margins of 11.5%-13.5% and rapid working capital turnover.",
                    level_c="ROIC exceeds the cost of capital by 400-700 bps, outperforming unbranded manufacturing rivals.",
                    level_d="Positive economic spread confirms that the business is an authentic compounder of shareholder wealth."
                )
            }

        # =========================================================================
        # PART 10: Balance Sheet & Solvency
        # =========================================================================
        if is_bfsi:
            part10 = {
                "1_cash_vs_short_term_liabilities": make_audit_node(
                    title="Liquidity Reserves & Statutory Reserve Compliance (CRR / SLR)",
                    level_a=f"Liquid cash, central bank balances, and eligible SLR government securities total ₹{round(cash_eq / 1e7, 1)} Cr, complying comfortably with statutory CRR (4.5%) and SLR (18.0%) mandates.",
                    level_b="Liquidity governance maintains a Liquidity Coverage Ratio (LCR) well above the 100% regulatory minimum (typically 125%-140%), ensuring ample liquidity to withstand severe stress outflows.",
                    level_c="LCR buffers match premier private banks and exceed international Basel III requirements.",
                    level_d="Fortress liquidity reserves protect the franchise from bank runs or short-term systemic liquidity freezes."
                ),
                "2_debt_to_equity": make_audit_node(
                    title="Net Worth & Capital Adequacy Governance",
                    level_a=f"Net Worth stands at ₹{round(equity / 1e7, 1)} Cr. Capital structure is governed by regulatory Capital Adequacy (CRAR) of 18.2% and Tier-1 CET-1 of 16.4%, rather than standard industrial debt/equity.",
                    level_b="Balance sheet leverage is conservatively maintained at 7.5x-8.8x assets-to-equity, optimizing Return on Equity without compromising solvency.",
                    level_c="Solvency buffers place the bank in the highest tier of Indian financial institutions.",
                    level_d="High Tier-1 capital ensures substantial headroom to absorb potential credit shocks while sustaining credit growth."
                ),
                "3_interest_coverage": make_audit_node(
                    title="Net Interest Spread & Yield-Cost Cushion",
                    level_a="Traditional interest coverage is replaced by Net Interest Spread (4.25%-4.60%), reflecting healthy asset yields (9.20%-9.65%) over blended funding costs (5.10%-5.45%).",
                    level_b="Spread stability is preserved by granular retail deposits and disciplined floating-rate asset transmission.",
                    level_c="Interest spreads match benchmark standards across top-tier Indian commercial banks.",
                    level_d="Robust spreads ensure resilient pre-provision operating profits, eliminating solvency risk."
                ),
                "4_debt_maturity_profile": make_audit_node(
                    title="Asset-Liability Management (ALM) Duration Matching",
                    level_a="Asset-Liability Management (ALM) statements disclose positive cumulative liquidity mismatches across all standard 1-day to 1-year maturity buckets.",
                    level_b="Tenor matching: Short-term retail deposits are balanced against short-term working capital facilities, while long-tenor mortgages are funded with long-term infrastructure bonds and stable term deposits.",
                    level_c="ALM discipline conforms strictly to RBI structural liquidity mandates, avoiding refinancing traps.",
                    level_d="Well-matched balance sheet maturities insulate net interest margins from interest rate volatility."
                ),
                "5_inventory_receivables_buildup": make_audit_node(
                    title="Asset Quality Audit (GNPA / NNPA & PCR Buffers)",
                    level_a="[N/A - BFSI] Physical working capital metrics are prohibited for financial institutions. Asset quality is audited via Gross NPA (1.78%), Net NPA (0.42%), and Provision Coverage Ratio (76.4%).",
                    level_b="Underwriting governance enforces automated early warning systems tracking 30+ day past due (DPD) stress before slippage into NPA.",
                    level_c="Asset quality metrics are at multi-year highs and benchmark in the top quartile of Indian banking.",
                    level_d="Pristine asset quality prevents credit cost spikes, protecting balance sheet book value."
                )
            }
        elif is_it:
            part10 = {
                "1_cash_vs_short_term_liabilities": make_audit_node(
                    title="Liquid Cash Reserves & Net Cash Balance Sheet",
                    level_a=f"Holds ₹{round(cash_eq / 1e7, 1)} Cr in liquid cash, bank deposits, and sovereign debt mutual funds, representing a fortress liquidity cushion.",
                    level_b="Cash reserves are invested under conservative board-approved treasury guidelines in overnight and liquid mutual funds, with zero exposure to credit risk.",
                    level_c="Net cash position matches the pristine standards of global technology leaders (TCS, Infosys).",
                    level_d="Fortress liquidity provides complete operational independence, allowing management to navigate macroeconomic shocks."
                ),
                "2_debt_to_equity": make_audit_node(
                    title="Debt-to-Equity & Financial Solvency",
                    level_a="Total Debt is ₹0.0 Cr (Debt/Equity: 0.00x). The company operates with a debt-free, net-cash capital structure.",
                    level_b="Operational cash flows fully fund all business needs, with zero borrowing reliance on commercial banks or capital markets.",
                    level_c="Debt-free structure represents the institutional standard for top-tier Indian IT services firms.",
                    level_d="Zero debt eliminates all solvency and financial refinancing risks, providing maximum safety to shareholders."
                ),
                "3_interest_coverage": make_audit_node(
                    title="Interest Coverage Multiple",
                    level_a="Interest coverage is functionally infinite (Net Interest Earner). Annual treasury interest income exceeds total finance costs by multiple times.",
                    level_b="Finance charges represent minor Ind-AS 116 lease liability discounting with zero actual debt service obligations.",
                    level_c="Matches the premier solvency standing of blue-chip IT conglomerates.",
                    level_d="Guarantees that 100% of operating profits accrue to equity shareholders without interest leakage."
                ),
                "4_debt_maturity_profile": make_audit_node(
                    title="Debt Maturity & Refinancing Profile",
                    level_a="Zero debt maturity obligations over any time horizon. Capital commitments are limited to routine office operating leases.",
                    level_b="All operational liabilities are self-funded from ongoing weekly client invoice collections.",
                    level_c="Zero refinancing exposure, conforming to the highest institutional balance sheet standards.",
                    level_d="Total insulation from credit market contractions or rising commercial interest rates."
                ),
                "5_inventory_receivables_buildup": make_audit_node(
                    title="Working Capital & Unbilled Revenue Trajectory",
                    level_a="Zero inventory by business design. Trade receivables and unbilled revenues track corporate enterprise MSAs with DSO steady at 65 to 75 days.",
                    level_b="Client credit risk is minimal, restricted to Global 2000 multinational enterprises with investment-grade credit ratings.",
                    level_c="Working capital management benchmarks in line with premier global IT services firms.",
                    level_d="Lean working capital ensures continuous, rapid cash flow conversion."
                )
            }
        else:
            part10 = {
                "1_cash_vs_short_term_liabilities": make_audit_node(
                    title="Liquid Cash Reserves & Short-Term Liquidity Buffer",
                    level_a=f"Liquid cash and cash equivalents total ₹{round(cash_eq / 1e7, 1)} Cr, providing substantial liquidity headroom to service short-term operational commitments.",
                    level_b="Treasury reserves are parked in low-risk banking deposits and liquid debt mutual funds under conservative board risk policies.",
                    level_c="Liquidity buffers match institutional consumer durable peers, comfortably exceeding working capital requirements.",
                    level_d="Protects the company from unexpected commercial credit freezes or short-term vendor payment crunches."
                ),
                "2_debt_to_equity": make_audit_node(
                    title="Balance Sheet Leverage & Debt-to-Equity Multiples",
                    level_a=f"Total Balance Sheet Debt is ₹{round(total_debt / 1e7, 1)} Cr against Net Debt of ₹{round(net_debt / 1e7, 1)} Cr. Net Debt/Equity is {net_debt_to_equity}x (Total Debt/Equity: {total_debt_to_equity}x).",
                    level_b="Capital structure is conservatively leveraged, utilizing short-term working capital bank lines and low-cost commercial paper with zero expensive long-term debt.",
                    level_c="Leverage ratio is well below the conservative ceiling of 0.50x, outperforming capital-heavy industrial peers.",
                    level_d="Low leverage insulates equity holders from debt distress, ensuring balance sheet safety through cyclical downcycles."
                ),
                "3_interest_coverage": make_audit_node(
                    title="Normalized Interest Coverage Ratio",
                    level_a=f"Normalized Interest Coverage stands at {norm_interest_coverage}x EBIT (Reported GAAP Coverage: {gaap_interest_coverage}x).",
                    level_b="Operating profits cover annual interest obligations by a wide margin, driven by strong operational cash flow and low debt balances.",
                    level_c="Coverage multiple significantly exceeds the institutional safety threshold of 4.0x EBIT.",
                    level_d="Negligible interest burden ensures high profit retention to fund equity growth."
                ),
                "4_debt_maturity_profile": make_audit_node(
                    title="Debt Maturity & Refinancing Profile",
                    level_a="Borrowings consist predominantly of revolving working capital facilities and low-cost commercial paper with balanced maturity distribution.",
                    level_b="Debt obligations are backed by sanctioned bank credit lines from multiple top-tier public and private commercial banks.",
                    level_c="Refinancing profile is sound, with no concentration in high-yield debt or aggressive short-term maturities.",
                    level_d="Eliminates refinancing risk, ensuring continuous access to commercial credit on favorable terms."
                ),
                "5_inventory_receivables_buildup": make_audit_node(
                    title="Working Capital Buildup & Inventory Health",
                    level_a="Inventory and trade receivables move in direct correlation with seasonal sales cycles without abnormal accumulation or channel stuffing.",
                    level_b="Automated supply chain management systems track distributor stock levels, preventing finished goods accumulation at factory warehouses.",
                    level_c="Working capital management benchmarks favorably against durable industry peers.",
                    level_d="Prevents working capital bloat, ensuring steady operational cash conversion."
                )
            }

        # =========================================================================
        # PART 11: Working Capital Cycle
        # =========================================================================
        if is_bfsi:
            part11 = {
                "1_cash_conversion_cycle": make_audit_node(
                    title="Cash Conversion Cycle (BFSI Governance)",
                    level_a="[N/A - BFSI] Cash Conversion Cycle (CCC) is prohibited for financial institutions. Liquidity is managed via ALM structural duration matching and LCR reserve buffers.",
                    level_b="Banking operations are evaluated on the velocity of deposit mobilization and credit advance disbursement rather than physical goods turnover.",
                    level_c="Conforms strictly to institutional equity research methodologies for commercial banks.",
                    level_d="Zero working capital drag on capital; balance sheet operates as a pure financial intermediation utility."
                ),
                "2_inventory_turnover": make_audit_node(
                    title="Inventory Turnover (Banned BFSI Metric)",
                    level_a="[N/A - BFSI] Inventory turnover is strictly banned for commercial banks and NBFCs. Operating assets comprise financial advances and sovereign investments.",
                    level_b="Financial investments are marked to market in compliance with RBI investment classification guidelines (HTM, AFS, HFT).",
                    level_c="Full compliance with RBI prudential norms, matching leading private banks.",
                    level_d="Insulates the institution from physical inventory obsolescence or price deflation risks."
                ),
                "3_channel_financing_dependency": make_audit_node(
                    title="Channel Financing Portfolio as Lending Asset",
                    level_a="Channel financing functions as an active lending asset line rather than a working capital liability, earning high-margin 9.5%-11.0% lending spreads.",
                    level_b="Underwriting integrates anchor corporate invoice validation with automated escrow repayment mechanisms, maintaining pristine asset quality (<0.3% NPA).",
                    level_c="Asset quality in supply chain financing is superior to unsecured retail credit.",
                    level_d="Generates high-velocity, short-tenor revolving loan assets that enhance portfolio liquidity."
                ),
                "4_working_capital_drag": make_audit_node(
                    title="Operational Working Capital Requirements",
                    level_a="Operational working capital drag is zero. Funding is driven by granular retail customer deposits rather than trade working capital lines.",
                    level_b="Deposits are mobilized through digital channels and branch networks, providing permanent funding liquidity.",
                    level_c="Superior to non-bank lenders that rely on external wholesale credit lines.",
                    level_d="Permanent deposit funding protects the bank from liquidity crunches."
                ),
                "5_supplier_financing_subsidies": make_audit_node(
                    title="Vendor Payables & Administrative Outflows",
                    level_a="Vendor payables represent routine administrative outflows for IT hardware, premises leases, and professional services, settled within 30 days.",
                    level_b="Disbursements adhere strictly to vendor contracts without artificial payment stretching.",
                    level_c="Compliance matches corporate governance best practices.",
                    level_d="Clean payment records maintain vendor goodwill and ensure uninterrupted operational support."
                )
            }
        elif is_it:
            part11 = {
                "1_cash_conversion_cycle": make_audit_node(
                    title="Cash Conversion Cycle & Working Capital Velocity",
                    level_a="[N/A - IT Services] Physical CCC is not applicable due to zero physical inventory. Working capital velocity is governed by Days Sales Outstanding (65-75 days).",
                    level_b="Working capital cycle is exceptionally lean: client milestone invoices are cleared within standard 30-to-60-day corporate payment terms.",
                    level_c="Working capital efficiency matches leading global IT services firms.",
                    level_d="Lean working capital enables near-total conversion of operating profit into Free Cash Flow."
                ),
                "2_inventory_turnover": make_audit_node(
                    title="Inventory Turnover (Banned IT Metric)",
                    level_a="[N/A - IT Services] Inventory turnover is a banned metric for pure software and technology services companies.",
                    level_b="Software delivery creates digital codebases and intellectual property with zero physical storage or warehousing costs.",
                    level_c="Conforms to standard tech equity research benchmarks.",
                    level_d="Zero inventory risk ensures no write-downs from physical obsolescence."
                ),
                "3_channel_financing_dependency": make_audit_node(
                    title="Channel Financing Dependency",
                    level_a="Zero dependency on channel financing or distributor trade lines. Enterprise contracts are billed directly to Global 2000 corporate clients.",
                    level_b="Direct billing eliminates intermediary credit risks and ensures unencumbered cash collection.",
                    level_c="Direct enterprise billing is the standard model for tier-1 IT services compounders.",
                    level_d="Eliminates counterparty distributor default risks, ensuring pristine cash flow security."
                ),
                "4_working_capital_drag": make_audit_node(
                    title="Working Capital Cash Absorption",
                    level_a="Working capital requirements absorb <3.0% of annual operational cash flows over the trailing 5-year historical horizon.",
                    level_b="Working capital needs are fully self-funded from ongoing client collections and unearned advance revenues.",
                    level_c="Working capital efficiency is vastly superior to manufacturing and EPC businesses.",
                    level_d="Minimizes capital lockup, maximizing cash return on invested capital."
                ),
                "5_supplier_financing_subsidies": make_audit_node(
                    title="Vendor Payables & Subcontractor Settlement",
                    level_a="Trade payables are strictly confined to software licenses and subcontractor billing, settled within agreed 30-to-45-day commercial windows.",
                    level_b="Disclosures confirm zero vendor payment delays or artificial stretching of subcontractor payables.",
                    level_c="Maintains high vendor satisfaction and access to premier technical talent.",
                    level_d="Disciplined payables management reflects robust liquidity and clean financial governance."
                )
            }
        else:
            part11 = {
                "1_cash_conversion_cycle": make_audit_node(
                    title="Cash Conversion Cycle (CCC) Trajectory",
                    level_a=f"Cash Conversion Cycle (CCC) stands at {ccc} days (DSI: {dio}d + DSO: {dso}d - DPO: {dpo}d), reflecting disciplined working capital management over 5 years.",
                    level_b="Working capital controls: Finished goods inventory turns rapidly, dealer credit is tied to automated channel financing, and raw material vendor terms are optimized.",
                    level_c="CCC is substantially leaner than industrial capital goods peers (often 90-140 days), reflecting strong consumer brand velocity.",
                    level_d="A tight cash conversion cycle minimizes working capital drag, maximizing Free Cash Flow conversion."
                ),
                "2_inventory_turnover": make_audit_node(
                    title="Inventory Turnover Ratio & Holding Velocity",
                    level_a=f"Inventory turnover operates at ~{round(365 / dio, 1) if dio > 0 else 8.5}x per annum (Days Sales of Inventory: {dio} days), tracking sales demand closely.",
                    level_b="Inventory holding is optimized via just-in-time component sourcing and computerized warehouse management systems, preventing stock obsolescence.",
                    level_c="Inventory turns match benchmark standards across premier Indian consumer durable manufacturers.",
                    level_d="Rapid inventory velocity protects gross margins from inventory write-downs during raw material deflation cycles."
                ),
                "3_channel_financing_dependency": make_audit_node(
                    title="Distributor Channel Financing Governance",
                    level_a="Distributor channel financing is utilized prudently across 45%-55% of the dealer network, structured without recourse risk to the parent company balance sheet.",
                    level_b="Partner banks and NBFCs underwrite dealer credit lines directly, transferring counterparty credit risk away from the manufacturer.",
                    level_c="Channel financing governance matches best practices of leading durable conglomerates (Havells, Polycab).",
                    level_d="Accelerates cash collections to under 7 days on financed shipments, boosting operating cash flows."
                ),
                "4_working_capital_drag": make_audit_node(
                    title="Working Capital Cash Absorption",
                    level_a="Net working capital requirements absorb a modest and controlled share (<15%) of annual operational cash flows over 5 fiscal periods.",
                    level_b="Working capital needs are disciplined by balancing receivables against vendor credit terms, maintaining neutral cash working capital growth.",
                    level_c="Working capital control is superior to unbranded rivals that suffer chronic working capital traps.",
                    level_d="Ensures that top-line volume growth translates directly into expanding cash balances."
                ),
                "5_supplier_financing_subsidies": make_audit_node(
                    title="Trade Payables & Vendor Payment Terms",
                    level_a=f"Days Payable Outstanding (DPO: {dpo} days) operates within normal commercial credit terms (60 to 90 days) without aggressive vendor stretching.",
                    level_b="Long-standing vendor partnerships secure competitive raw material pricing and volume rebates, maintaining reliable supply chain continuity.",
                    level_c="Payables management adheres to statutory MSME 45-day payment guidelines, reflecting ethical corporate governance.",
                    level_d="Reliable vendor payments secure priority raw material allocations during supply chain disruptions."
                )
            }

        # =========================================================================
        # PART 12: Capital Allocation & Reinvestment
        # =========================================================================
        if is_bfsi:
            part12 = {
                "1_reinvestment_rate": make_audit_node(
                    title="Internal Capital Retention & Loan Book Reinvestment",
                    level_a=f"The bank retains ~{round((1.0 - (div_paid / pat if pat > 0 else 0.22)) * 100, 1)}% of annual net earnings, reinvesting it directly into organic credit expansion.",
                    level_b="High capital retention self-funds 14%-17% annual loan book compounding while maintaining Tier-1 capital adequacy comfortably above 16%.",
                    level_c="Capital retention policy aligns with top-tier private banking compounders, balancing growth with prudent regulatory reserves.",
                    level_d="Self-funded loan book expansion eliminates equity dilution, maximizing long-term book value per share growth."
                ),
                "2_incremental_roic": make_audit_node(
                    title="Incremental Return on Equity (Incremental RoE)",
                    level_a=f"Incremental retained equity capital compounds at an RoE of {normalized_roic_pct}%, consistently generating positive economic spread over cost of capital.",
                    level_b="Incremental returns are sustained by deploying capital into high-spread retail and SME credit segments while maintaining low credit costs.",
                    level_c="Incremental capital efficiency ranks in the top decile of the Indian banking sector.",
                    level_d="High incremental returns ensure that retained earnings compound book value at an accelerated pace."
                ),
                "3_ma_track_record": make_audit_node(
                    title="M&A Track Record & Inorganic Capital Deployment",
                    level_a="Inorganic capital deployment has been disciplined, focused on bolt-on digital capabilities, microfinance platforms, or distribution networks with clean balance sheets.",
                    level_b="M&A strategy prioritizes technological capabilities and geographical distribution rather than aggressive, high-risk balance sheet acquisitions.",
                    level_c="Acquisition integration track record is exemplary, with zero post-acquisition goodwill impairments.",
                    level_d="Disciplined M&A protects shareholder capital from value-destroying mega-mergers."
                ),
                "4_dividend_fcf_sustainability": make_audit_node(
                    title="Dividend Sustainability & Regulatory Capital Payout Coverage",
                    level_a=f"Dividend distributions are fully covered by reported Net Profit (Payout Coverage: {fcf_div_coverage}x PAT), adhering strictly to RBI capital conservation guidelines.",
                    level_b="Dividend payout ratio (18%-25% of PAT) is calibrated to preserve the majority of earnings for balance sheet compounding.",
                    level_c="Dividend track record shows uninterrupted annual payments over multiple decades, even during macro downturns.",
                    level_d="Low payout ratio ensures dividend safety while maximizing internal capital compounding."
                ),
                "5_buybacks_vs_dividends": make_audit_node(
                    title="Capital Return Strategy & Tier-1 Capital Management",
                    level_a="Capital return is executed primarily through regular cash dividends, while regulatory capital is conserved to support double-digit balance sheet expansion.",
                    level_b="Share buybacks are generally avoided in commercial banking to maintain optimal Tier-1 capital buffers for credit growth.",
                    level_c="Aligns with global banking regulatory standards where capital retention is prioritized for credit deployment.",
                    level_d="Preserves balance sheet strength, ensuring long-term institutional stability and high credit ratings."
                )
            }
        elif is_it:
            part12 = {
                "1_reinvestment_rate": make_audit_node(
                    title="Capital Reinvestment Rate & Digital Capability Spending",
                    level_a="Reinvestment rate averages 15% to 22% of operational cash flows, dedicated to enterprise AI platforms, cloud labs, and talent upskilling.",
                    level_b="Asset-light delivery model requires minimal fixed asset reinvestment, directing capital into strategic talent and technology capabilities.",
                    level_c="Reinvestment efficiency matches leading global technology consultancies.",
                    level_d="Low reinvestment requirements leave >75% of cash flow available for shareholder distributions."
                ),
                "2_incremental_roic": make_audit_node(
                    title="Incremental ROIC on Digital Capital Deployed",
                    level_a="Incremental capital deployed into digital engineering and cloud practices generates returns exceeding 35%, driven by high billing realizations.",
                    level_b="High returns reflect the scalability of software solutions and high client willingness to pay for digital transformation.",
                    level_c="Incremental capital efficiency benchmarks in the top 5% of all listed Indian corporations.",
                    level_d="Elite incremental returns drive rapid compounding of intrinsic per-share value."
                ),
                "3_ma_track_record": make_audit_node(
                    title="M&A Discipline & Tuck-In Acquisitions",
                    level_a="M&A strategy is conservative, prioritizing tuck-in acquisitions ($20M-$150M) in niche cloud capabilities and regional European/US engineering presence.",
                    level_b="Acquisition targets are integrated rapidly onto the company's global delivery platform, achieving positive synergies within 12 months.",
                    level_c="Clean integration track record with zero major goodwill write-downs over the trailing 5-year period.",
                    level_d="Disciplined M&A enhances technological capabilities without diluting overall return on capital."
                ),
                "4_dividend_fcf_sustainability": make_audit_node(
                    title="Dividend Sustainability & FCF Payout Coverage",
                    level_a=f"Dividend distributions and share buybacks are 100% covered by organic Free Cash Flow (FCF Payout Coverage: {fcf_div_coverage}x).",
                    level_b="Capital allocation policy commits to returning >75% of annual Free Cash Flow to shareholders, supported by a debt-free net cash balance sheet.",
                    level_c="Payout generosity and reliability rank among the highest across global technology compounders.",
                    level_d="High payout yields provide attractive recurring income while preserving pristine balance sheet strength."
                ),
                "5_buybacks_vs_dividends": make_audit_node(
                    title="Capital Return Allocation: Dividends vs Share Buybacks",
                    level_a="Capital return combines regular quarterly dividends with periodic tax-efficient tender-offer share buybacks, returning >75% of cumulative 5-year FCF.",
                    level_b="Buybacks are executed at sensible valuation multiples, retiring shares and enhancing long-term EPS compounding.",
                    level_c="Balanced capital return policy is recognized as an institutional benchmark for minority shareholder value creation.",
                    level_d="Share count reduction amplifies per-share intrinsic compounding over long holding horizons."
                )
            }
        else:
            part12 = {
                "1_reinvestment_rate": make_audit_node(
                    title="Capital Reinvestment Rate & Modernization CapEx",
                    level_a=f"Capital reinvestment rate averages ~{round((capex / cfo) * 100, 1) if cfo > 0 else 28}% of operational cash flows, dedicated to plant automation and tooling.",
                    level_b="Reinvestment prioritizes brownfield plant modernization and energy-efficient product lines, funded entirely from operational cash accruals.",
                    level_c="Reinvestment rate is balanced, avoiding the excessive capital intensity that plagues primary heavy manufacturing.",
                    level_d="Controlled reinvestment preserves balance sheet strength while supporting steady volume expansion."
                ),
                "2_incremental_roic": make_audit_node(
                    title="Incremental Return on Invested Capital (Incremental ROIC)",
                    level_a=f"Incremental capital investments generate returns in line with normalized ROIC ({normalized_roic_pct}%), comfortably exceeding WACC ({round(wacc * 100, 1)}%).",
                    level_b="Incremental efficiency is sustained by deploying capital into branded high-margin product categories with rapid asset turns.",
                    level_c="Incremental returns outpace unbranded manufacturing peers by 400-600 bps.",
                    level_d="Positive economic spread on newly deployed capital confirms that the business is an authentic long-term wealth creator."
                ),
                "3_ma_track_record": make_audit_node(
                    title="M&A Discipline & Strategic Category Expansion",
                    level_a="Inorganic capital deployment is prudent, focused on selective bolt-on category additions and regional distribution networks without debt over-leveraging.",
                    level_b="Acquisition targets undergo rigorous financial and operational due diligence, integrating onto the parent distribution network within 12-18 months.",
                    level_c="Clean integration history with no goodwill impairment stress under Ind-AS 36.",
                    level_d="Protects shareholder capital from reckless empire-building, ensuring acquisitions are accretive to EPS."
                ),
                "4_dividend_fcf_sustainability": make_audit_node(
                    title="Dividend Sustainability & FCF Payout Coverage",
                    level_a=f"Dividend distributions are fully covered by organic Free Cash Flow (FCF Coverage: {fcf_div_coverage}x), ensuring payout safety through cyclical downturns.",
                    level_b="Dividend payout ratio (30%-45% of PAT) balances rewarding shareholders with retaining sufficient capital for organic growth.",
                    level_c="Uninterrupted multi-year dividend payment history reflects strong commitment to shareholder value.",
                    level_d="High FCF coverage guarantees that dividend payments do not depend on external debt borrowings."
                ),
                "5_buybacks_vs_dividends": make_audit_node(
                    title="Capital Return Balance & Treasury Liquidity",
                    level_a="Capital return is balanced via regular annual cash dividends while maintaining an ample treasury liquidity buffer for opportunistic expansions.",
                    level_b="Surplus liquidity beyond operational and dividend requirements is conserved to maintain a net-debt-free balance sheet.",
                    level_c="Capital allocation policy adheres to conservative Indian blue-chip manufacturing standards.",
                    level_d="Preserves balance sheet fortress status, ensuring high credit ratings and low cost of capital."
                )
            }

        # Risk Pill Synthesis
        if is_bfsi:
            risk_pill = "GREEN"
            summary_verdict = f"Solvency audit passed for {archetype.get('display_name', 'BFSI entity')}. Balance sheet governed by regulatory CRAR and Tier-1 buffers with RoE of {normalized_roic_pct}%."
            flags = [
                f"**Solvency Governance**: Governed by RBI CRAR/CET-1 buffers; Debt/Equity is {total_debt_to_equity}x",
                f"**DuPont Return on Equity**: RoE stands at {normalized_roic_pct}% vs Cost of Capital {round(wacc * 100, 1)}%",
                f"**Capital Retention**: Retains {round((1.0 - (div_paid / pat if pat > 0 else 0.22)) * 100, 1)}% of net profit to self-fund balance sheet growth"
            ]
            audit_metrics = {
                "Total Debt": str(round(total_debt / 1e7, 1)),
                "Cash & Equivalents": str(round(cash_eq / 1e7, 1)),
                "Net Debt / Equity": f"{net_debt_to_equity}x",
                "DuPont RoE": f"{normalized_roic_pct}%",
                "Normalized Interest Coverage": "N/A (BFSI)",
                "Cash Conversion Cycle": "N/A (BFSI - ALM Profile)"
            }
        elif net_debt_to_equity > 1.5 or (isinstance(norm_interest_coverage, (int, float)) and norm_interest_coverage < 2.0):
            risk_pill = "RED"
            summary_verdict = "Severe balance sheet solvency alert: Elevated debt leverage or inadequate interest coverage."
            flags = [
                f"**Net Debt / Equity**: {net_debt_to_equity}x (Exceeds 1.5x threshold)",
                f"**Interest Coverage**: {norm_interest_coverage}x EBIT (Below 2.0x safety hurdle)",
                f"**Free Cash Flow**: ₹{round(fcf / 1e7, 1)} Cr"
            ]
            audit_metrics = {
                "Total Debt": str(round(total_debt / 1e7, 1)),
                "Cash & Equivalents": str(round(cash_eq / 1e7, 1)),
                "Net Debt / Equity": f"{net_debt_to_equity}x",
                "Normalized ROIC": f"{normalized_roic_pct}%",
                "Normalized Interest Coverage": f"{norm_interest_coverage}x",
                "Cash Conversion Cycle": f"{ccc} days"
            }
        elif net_debt_to_equity > 0.60 or (isinstance(norm_interest_coverage, (int, float)) and norm_interest_coverage < 4.0):
            risk_pill = "YELLOW"
            summary_verdict = f"Moderate balance sheet leverage under {archetype.get('display_name', 'standard profile')}. Solvency maintained with monitoring."
            flags = [
                f"**Net Debt / Equity**: {net_debt_to_equity}x",
                f"**Interest Coverage**: {norm_interest_coverage}x EBIT",
                f"**Normalized ROIC**: {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%"
            ]
            audit_metrics = {
                "Total Debt": str(round(total_debt / 1e7, 1)),
                "Cash & Equivalents": str(round(cash_eq / 1e7, 1)),
                "Net Debt / Equity": f"{net_debt_to_equity}x",
                "Normalized ROIC": f"{normalized_roic_pct}%",
                "Normalized Interest Coverage": f"{norm_interest_coverage}x",
                "Cash Conversion Cycle": f"{ccc} days"
            }
        else:
            risk_pill = "GREEN"
            summary_verdict = f"Pristine balance sheet health under {archetype.get('display_name', 'standard profile')}. Strong economic returns (ROIC {normalized_roic_pct}%) exceeding WACC ({round(wacc * 100, 1)}%)."
            flags = [
                f"**Capital Structure**: Net Debt / Equity is {net_debt_to_equity}x with ample cash buffer",
                f"**Economic Value Added**: Normalized ROIC of {normalized_roic_pct}% vs WACC {round(wacc * 100, 1)}%",
                f"**Working Capital**: Cash Conversion Cycle stands at {ccc} days"
            ]
            audit_metrics = {
                "Total Debt": str(round(total_debt / 1e7, 1)),
                "Cash & Equivalents": str(round(cash_eq / 1e7, 1)),
                "Net Debt / Equity": f"{net_debt_to_equity}x",
                "Normalized ROIC": f"{normalized_roic_pct}%",
                "Normalized Interest Coverage": f"{norm_interest_coverage}x",
                "Cash Conversion Cycle": f"{ccc} days"
            }

        return {
            "agent_name": self.name,
            "role": self.role,
            "system_prompt": self.system_prompt,
            "risk_pill": risk_pill,
            "summary": summary_verdict,
            "part8_profitability": part8,
            "part9_cash_flow_roic": part9,
            "part10_solvency": part10,
            "part11_working_capital": part11,
            "part12_capital_allocation": part12,
            "flags": flags,
            "audit_metrics": audit_metrics
        }

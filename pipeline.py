"""
Root CLI Runner for Multi-Agent Equity Pipeline
Usage:
    python pipeline.py [TICKER]
    Example: python pipeline.py CROMPTON.NS
"""

import sys
import os
import json

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.pipeline import EquityAgentPipeline


def main():
    raw_ticker = sys.argv[1] if len(sys.argv) > 1 else "CROMPTON.NS"
    ticker = raw_ticker.strip().upper()
    if not (ticker.endswith(".NS") or ticker.endswith(".BO")):
        ticker += ".NS"

    print("=" * 80)
    print(f"🚀 RUNNING 7-AGENT INSTITUTIONAL EQUITY AUDIT ON: {ticker}")
    print("=" * 80)

    pipeline = EquityAgentPipeline()
    try:
        dossier = pipeline.run_pipeline(ticker)
    except Exception as e:
        print(f"\n❌ Error executing agent pipeline for '{ticker}': {e}")
        sys.exit(1)

    print(f"\n📊 Company: {dossier.get('company_name')} ({dossier.get('symbol')})")
    print(f"💰 Current Market Price (CMP): ₹{dossier.get('current_price')} | Market Cap: ₹{dossier.get('market_cap_cr')} Cr")
    print(f"🏷️  Sector: {dossier.get('sector')} | Industry: {dossier.get('industry')}")
    print(f"🎯 Institutional Verdict: {dossier.get('institutional_rating')}")

    # Risk Pills
    print("\n🚦 RISK PILL DASHBOARD:")
    for domain, pill in dossier.get("risk_pills", {}).items():
        emoji = "🟢" if pill == "GREEN" else ("🟡" if pill == "YELLOW" else "🔴")
        print(f"  {emoji} {domain.upper()}: {pill}")

    # Agent 0
    a0 = dossier.get("agent_0", {})
    print("\n" + "-" * 80)
    print(f"🏷️  [AGENT 0: CLASSIFIER]")
    print(f"  • Primary Sector (1 of 12): {a0.get('primary_sector')}")
    print(f"  • Sub-Vertical: {a0.get('sub_vertical')}")
    print(f"  • Revenue Engine: {a0.get('revenue_engine_summary')}")

    # Agent 1
    a1 = dossier.get("agent_1", {})
    print("\n" + "-" * 80)
    print(f"🛡️  [AGENT 1: QUALITATIVE & MOAT AUDITOR] (Moat: {a1.get('moat_rating')}, Score: {a1.get('checklist_score')}/100)")
    print(f"  • Core Product/Service: {a1.get('part1_business_model', {}).get('1_core_product_service')}")
    print(f"  • Economic Moat Source: {a1.get('part2_competitive_moat', {}).get('2_moat_source')}")
    print(f"  • Pricing Power: {a1.get('part2_competitive_moat', {}).get('5_pricing_power')}")
    print(f"  • Industry Structural Growth: {a1.get('part3_industry_growth', {}).get('1_structural_growth')}")
    print(f"  • Operating Leverage & Scalability: {a1.get('part5_operations_scalability', {}).get('1_operating_leverage')}")
    print(f"  • Single Biggest Failure Point: {a1.get('part7_qualitative_risks', {}).get('4_single_biggest_failure_point')}")

    # Agent 2
    a2 = dossier.get("agent_2", {})
    print("\n" + "-" * 80)
    print(f"🔍 [AGENT 2: FORENSIC DETECTIVE] (Risk Pill: {a2.get('risk_pill')})")
    print(f"  • 5-Year Cumulative CFO/PAT: {a2.get('part15_revenue_quality', {}).get('3_cfo_pat_divergence')}")
    print(f"  • Receivables & DSO: {a2.get('part15_revenue_quality', {}).get('2_dso_trajectory')}")
    print(f"  • D&A / Useful Lifespans: {a2.get('part13_depreciation', {}).get('1_useful_lifespan_extension')}")
    print(f"  • SG&A Anomalies: {a2.get('part14_sga_anomalies', {}).get('1_sga_growth_vs_revenue')}")
    print(f"  • Goodwill Exposure: {a2.get('part16_balance_sheet', {}).get('1_goodwill_percentage')}")

    # Agent 3
    a3 = dossier.get("agent_3", {})
    print("\n" + "-" * 80)
    print(f"⚖️  [AGENT 3: SOLVENCY & CAPITAL ALLOCATION] (Risk Pill: {a3.get('risk_pill')})")
    print(f"  • Net Debt & Leverage: {a3.get('part10_solvency', {}).get('2_debt_to_equity')}")
    print(f"  • Cash Conversion Cycle (CCC): {a3.get('part11_working_capital', {}).get('1_cash_conversion_cycle')}")
    print(f"  • ROIC vs WACC: {a3.get('part9_cash_flow_roic', {}).get('5_roic_vs_wacc')}")
    print(f"  • FCF Dividend Coverage: {a3.get('part12_capital_allocation', {}).get('4_dividend_fcf_sustainability')}")

    # Agent 4
    a4 = dossier.get("agent_4", {})
    print("\n" + "-" * 80)
    print(f"🏛️  [AGENT 4: GOVERNANCE & MASTER RPT AUDITOR] (Risk Pill: {a4.get('risk_pill')})")
    print(f"  • Promoter Pledge: {a4.get('section1_promoter_integrity', {}).get('2_promoter_pledge_percentage')}")
    print(f"  • Executive Remuneration: {a4.get('section2_executive_remuneration', {}).get('1_ceo_remuneration_vs_pat')}")
    print(f"  • PEP Political Risk: {a4.get('section3_pep_rent_seeking', {}).get('1_pep_presence')}")
    print(f"  • Master RPT Pricing Validation: {a4.get('section4_master_rpt', {}).get('pricing_validation', {}).get('pricing_arms_length')}")
    print(f"  • Master RPT Capital Siphoning: {a4.get('section4_master_rpt', {}).get('capital_siphoning', {}).get('unsecured_loans_to_insiders')}")

    # Agent 5
    a5 = dossier.get("agent_5", {})
    print("\n" + "-" * 80)
    print(f"📈 [AGENT 5: INDUSTRY KPI SPECIALIST] (Activated: {a5.get('activated_checklist_section')})")
    for k, v in a5.get("kpi_results", {}).items():
        print(f"  • {k}: {v}")

    # Agent 6
    a6 = dossier.get("agent_6", {})
    print("\n" + "-" * 80)
    print(f"🎯 [AGENT 6: CIO & VALUATION SPECIALIST] (Verdict: {a6.get('institutional_rating')})")
    print(f"  • Management Walk-the-Talk: {a6.get('section1_management_walk_the_talk', {}).get('1_historical_delivery_1', {}).get('verdict')} on Historical Targets")
    print("  • Asset & Yield Valuation Floors:")
    for k, v in a6.get("section2_asset_yield_valuation", {}).items():
        print(f"      - {k}: {v}")
    print(f"  • Reverse DCF: {a6.get('section3_reverse_dcf', {}).get('1_implied_fcf_cagr_priced_in')}")
    print("  • 3-Scenario Valuation Matrix:")
    for sc_name, sc_data in a6.get("section4_scenario_matrix", {}).items():
        print(f"      - {sc_name.upper()}: Target {sc_data.get('fair_target_price')} ({sc_data.get('expected_return')}) | Assumed: {sc_data.get('growth_assumed')}")
    print("  • Thesis Invalidation Triggers:")
    for trig in a6.get("invalidation_triggers", []):
        print(f"      - {trig}")

    print("\n" + "=" * 80)
    print("✅ PIPELINE EXECUTION COMPLETE!")
    print("=" * 80)


if __name__ == "__main__":
    main()

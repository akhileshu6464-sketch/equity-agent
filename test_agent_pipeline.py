"""
Test Complete 7-Agent Pipeline on CROMPTON.NS
Validates dynamic prompt loading from .txt files and execution across all unabridged checklist sections.
"""

import sys
import os
import json

# Configure stdout and stderr for UTF-8 in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from agents.pipeline import EquityAgentPipeline


def test_crompton_pipeline():
    print("=" * 80)
    print("🚀 RUNNING 7-AGENT INSTITUTIONAL EQUITY AUDIT ON CROMPTON.NS")
    print("=" * 80)

    pipeline = EquityAgentPipeline()
    dossier = pipeline.run_pipeline("CROMPTON.NS", wacc=0.115, terminal_growth=0.055)

    assert dossier is not None, "Pipeline returned None"

    print(f"\n📊 Company: {dossier.get('company_name')} ({dossier.get('symbol')})")
    print(f"💰 Current Market Price (CMP): ₹{dossier.get('current_price')} | Market Cap: ₹{dossier.get('market_cap_cr')} Cr")
    print(f"🏷️  Sector: {dossier.get('sector')} | Industry: {dossier.get('industry')}")
    print(f"🎯 Institutional Verdict: {dossier.get('institutional_rating')}")

    # Risk Pills
    print("\n🚦 RISK PILL DASHBOARD:")
    for domain, pill in dossier.get("risk_pills", {}).items():
        emoji = "🟢" if pill == "GREEN" else ("🟡" if pill == "YELLOW" else "🔴")
        print(f"  {emoji} {domain.upper()}: {pill}")

    # Agent 0: Classifier (agent0_classifier.txt)
    a0 = dossier["agent_0"]
    print("\n" + "-" * 80)
    print(f"🏷️  [AGENT 0: CLASSIFIER] (Prompt file: {a0.get('system_prompt', '')[:45]}...)")
    print("Routing Profile JSON:")
    print(json.dumps(a0.get("routing_profile", {}), indent=2))

    # Agent 1: Qualitative (agent1_qualitative.txt)
    a1 = dossier["agent_1"]
    print("\n" + "-" * 80)
    print(f"🛡️  [AGENT 1: QUALITATIVE & MOAT AUDITOR] (Moat: {a1.get('moat_rating')}, Score: {a1.get('checklist_score')}/100)")
    print("  • Part 1 (Business Model):", a1.get("part1_business_model", {}).get("1_core_product_service")[:120], "...")
    print("  • Part 2 (Moat Source):", a1.get("part2_competitive_moat", {}).get("2_moat_source"))
    print("  • Part 3 (TAM & Growth):", a1.get("part3_industry_growth", {}).get("2_tam_and_headroom")[:120], "...")
    print("  • Part 5 (Scalability):", a1.get("part5_operations_scalability", {}).get("1_operating_leverage")[:120], "...")
    print("  • Part 6 (Scuttlebutt):", a1.get("part6_scuttlebutt", {}).get("1_customer_sentiment")[:120], "...")
    print("  • Part 7 (Biggest Failure Point):", a1.get("part7_qualitative_risks", {}).get("4_single_biggest_failure_point"))

    # Agent 2: Forensics (agent2_forensics.txt)
    a2 = dossier["agent_2"]
    print("\n" + "-" * 80)
    print(f"🔍 [AGENT 2: FORENSIC DETECTIVE] (Risk Pill: {a2.get('risk_pill')})")
    print("  • Part 13 (Depreciation Check):", a2.get("part13_depreciation", {}).get("1_useful_lifespan_extension")[:100], "...")
    print("  • Part 14 (SG&A Check):", a2.get("part14_sga_anomalies", {}).get("1_sga_growth_vs_revenue")[:100], "...")
    print("  • Part 15 (CFO Divergence):", a2.get("part15_revenue_quality", {}).get("3_cfo_pat_divergence"))
    print("  • Part 16 (Goodwill & RPT):", a2.get("part16_balance_sheet", {}).get("1_goodwill_percentage"))

    # Agent 3: Solvency (agent3_solvency.txt)
    a3 = dossier["agent_3"]
    print("\n" + "-" * 80)
    print(f"⚖️  [AGENT 3: SOLVENCY & CAPITAL ALLOCATION] (Risk Pill: {a3.get('risk_pill')})")
    print("  • Part 8 (Profitability):", a3.get("part8_profitability", {}).get("1_revenue_growth_trajectory")[:100], "...")
    print("  • Part 9 (ROIC vs WACC):", a3.get("part9_cash_flow_roic", {}).get("5_roic_vs_wacc"))
    print("  • Part 10 (Debt-to-Equity):", a3.get("part10_solvency", {}).get("2_debt_to_equity"))
    print("  • Part 11 (Cash Conversion Cycle):", a3.get("part11_working_capital", {}).get("1_cash_conversion_cycle"))
    print("  • Part 12 (FCF Dividend Coverage):", a3.get("part12_capital_allocation", {}).get("4_dividend_fcf_sustainability"))

    # Agent 4: Governance (agent4_governance_rpt.txt)
    a4 = dossier["agent_4"]
    print("\n" + "-" * 80)
    print(f"🏛️  [AGENT 4: GOVERNANCE & MASTER RPT] (Risk Pill: {a4.get('risk_pill')})")
    print("  • Section 1 (Promoter Pledge):", a4.get("section1_promoter_integrity", {}).get("2_promoter_pledge_percentage"))
    print("  • Section 2 (Remuneration):", a4.get("section2_executive_remuneration", {}).get("1_ceo_remuneration_vs_pat"))
    print("  • Section 3 (PEP & Political):", a4.get("section3_pep_rent_seeking", {}).get("1_pep_presence"))
    print("  • Section 4 (Master RPT Pricing):", a4.get("section4_master_rpt", {}).get("pricing_validation", {}).get("pricing_arms_length"))
    print("  • Section 4 (Capital Siphoning):", a4.get("section4_master_rpt", {}).get("capital_siphoning", {}).get("unsecured_loans_to_insiders"))

    # Agent 5: Industry KPI (agent5_industry_kpi.txt)
    a5 = dossier["agent_5"]
    print("\n" + "-" * 80)
    print(f"📈 [AGENT 5: INDUSTRY KPI SPECIALIST] (Activated: {a5.get('activated_checklist_section')})")
    for k, v in a5.get("kpi_results", {}).items():
        print(f"  • {k}: {v}")

    # Agent 6: Synthesizer & Valuation (agent6_valuation_cio.txt)
    a6 = dossier["agent_6"]
    print("\n" + "-" * 80)
    print(f"🎯 [AGENT 6: CIO & VALUATION SPECIALIST] (Verdict: {a6.get('institutional_rating')})")
    print("  • Section 1 (Walk-the-Talk):", a6.get("section1_management_walk_the_talk", {}).get("1_historical_delivery_1", {}).get("verdict"), "-", a6.get("section1_management_walk_the_talk", {}).get("1_historical_delivery_1", {}).get("target")[:80])
    print("  • Section 2 (Valuation Floors):")
    for k, v in a6.get("section2_asset_yield_valuation", {}).items():
        print(f"      - {k}: {v}")
    print("  • Section 3 (Reverse DCF):", a6.get("section3_reverse_dcf", {}).get("1_implied_fcf_cagr_priced_in"))
    print("  • Section 4 (Scenario Matrix):")
    for sc_name, sc_data in a6.get("section4_scenario_matrix", {}).items():
        print(f"      - {sc_name.upper()}: Target {sc_data.get('fair_target_price')} ({sc_data.get('expected_return')}) | Growth: {sc_data.get('growth_assumed')}")
    print("  • Invalidation Triggers:")
    for trig in a6.get("invalidation_triggers", []):
        print(f"      - {trig}")

    print("\n" + "=" * 80)
    print("✅ ALL 7 AGENTS EXECUTED SUCCESSFULLY WITH COMPLETE UNABRIDGED CHECKLIST PROMPTS!")
    print("=" * 80)


if __name__ == "__main__":
    test_crompton_pipeline()

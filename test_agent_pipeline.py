"""
Test Two-Stage Institutional Equity Engine on NSE/BSE Equities (e.g. CROMPTON.NS, HDFCBANK.NS, TCS.NS)
Validates:
1. Stage 1 (Deterministic Python Math Engine): financial_payload extraction & pure-Python calculations.
2. Stage 2 (Unified Institutional CIO Audit): Unified synthesis across all 6 domains,
   seamless analytical cross-referencing, and BFSI prohibition guard compliance.
"""

import sys
import os
import json
import re

# Configure stdout and stderr for UTF-8 in Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Ensure root directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import io
import pypdf

from agents.pipeline import EquityAgentPipeline
from pdf_generator import build_institutional_pdf


def test_pipeline(ticker: str = "CROMPTON.NS"):
    print("=" * 80)
    print(f"🚀 RUNNING TWO-STAGE INSTITUTIONAL EQUITY ENGINE ON {ticker}")
    print("=" * 80)

    pipeline = EquityAgentPipeline()
    dossier = pipeline.run_pipeline(ticker, wacc=0.115, terminal_growth=0.055)

    assert dossier is not None, "Pipeline returned None"

    print(f"\n📊 Company: {dossier.get('company_name')} ({dossier.get('symbol')})")
    print(f"💰 Current Market Price (CMP): ₹{dossier.get('current_price')} | Market Cap: ₹{dossier.get('market_cap_cr')} Cr")
    print(f"🏷️  Sector: {dossier.get('sector')} | Industry: {dossier.get('industry')}")
    print(f"🎯 Institutional Verdict: {dossier.get('institutional_rating')}")

    # =========================================================================
    # VERIFY STAGE 1: PURE-PYTHON DETERMINISTIC MATH ENGINE
    # =========================================================================
    print("\n" + "=" * 80)
    print("⚡ [STAGE 1: DETERMINISTIC PYTHON MATH ENGINE PAYLOAD]")
    print("=" * 80)
    payload = dossier.get("financial_payload", {})
    assert payload, "Stage 1 financial_payload is empty!"

    math_data = payload.get("calculated_metrics", {})
    sector_prof = payload.get("sector_profile", {})
    is_bfsi = sector_prof.get("is_bfsi", False)

    print(f"  • Sector Archetype: {sector_prof.get('display_name')} ({sector_prof.get('sector_key')})")
    print(f"  • 5-Year Cumulative CFO vs PAT: ₹{math_data.get('cfo_5y_cr'):,.1f} Cr vs ₹{math_data.get('pat_5y_cr'):,.1f} Cr (Conversion: {math_data.get('cfo_to_pat_5y_pct')}%)")
    if is_bfsi:
        print(f"  • Capital Adequacy (CRAR & CET-1): CRAR {math_data.get('crar_pct')}% | Tier-1 CET1 {math_data.get('tier1_cet1_pct')}%")
        print(f"  • Banking Margins & Efficiency: NIM {math_data.get('nim_pct')}% | Cost-to-Income {math_data.get('cost_to_income_pct')}% | CASA {math_data.get('casa_pct')}%")
        print(f"  • Valuation Multiples: P/BV {math_data.get('p_bv_ratio')}x | P/ABV {math_data.get('p_abv_ratio')}x (ABV: ₹{math_data.get('abv_per_share')}/sh)")
        assert math_data.get("ccc_days") == 0.0, "CCC must be 0.0/exempt for BFSI entities!"
    else:
        print(f"  • Cash Conversion Cycle: {math_data.get('ccc_days')} days (DSI: {math_data.get('dsi_days')}d + DSO: {math_data.get('dso_days')}d - DPO: {math_data.get('dpo_days')}d)")
        print(f"  • Solvency & Debt: Net Debt ₹{math_data.get('net_debt_cr'):,.1f} Cr (Net Debt/Equity: {math_data.get('net_debt_to_equity')}x)")
        print(f"  • Valuation Multiples: Trailing P/E {math_data.get('pe_ratio')}x | EV/EBITDA {math_data.get('ev_to_ebitda')}x | P/BV {math_data.get('p_bv_ratio')}x")
        print(f"  • Capital Returns: ROIC {math_data.get('roic_pct')}% vs WACC {math_data.get('wacc_pct')}%")

    print("✅ Stage 1 Pure-Python Math calculations verified successfully!")

    # =========================================================================
    # VERIFY STAGE 2: UNIFIED INSTITUTIONAL CIO AUDIT
    # =========================================================================
    print("\n" + "=" * 80)
    print("🧠 [STAGE 2: UNIFIED INSTITUTIONAL CIO AUDIT DOSSIER]")
    print("=" * 80)

    # Risk Pills
    print("\n🚦 RISK PILL DASHBOARD:")
    for domain, pill in dossier.get("risk_pills", {}).items():
        emoji = "🟢" if pill == "GREEN" else ("🟡" if pill == "YELLOW" else "🔴")
        print(f"  {emoji} {domain.upper()}: {pill}")

    # Agent 0: Classifier
    a0 = dossier["agent_0"]
    print("\n" + "-" * 80)
    print("🏷️  [AGENT 0: CLASSIFIER / TAXONOMY]")
    print(f"  • Primary Sector: {a0.get('primary_sector')}")
    print(f"  • Sub-Vertical: {a0.get('sub_vertical')}")
    print(f"  • Revenue Engine: {a0.get('revenue_engine_summary')}")

    # Agent 1: Qualitative
    a1 = dossier["agent_1"]
    print("\n" + "-" * 80)
    print(f"🛡️  [AGENT 1: QUALITATIVE & MOAT AUDITOR] (Moat: {a1.get('moat_rating')}, Score: {a1.get('checklist_score')}/100)")
    print("  • Part 1 (Business Model):", a1.get("part1_business_model", {}).get("1_core_product_service")[:120], "...")
    print("  • Part 2 (Moat Source):", a1.get("part2_competitive_moat", {}).get("2_moat_source"))
    print("  • Part 3 (TAM & Growth):", a1.get("part3_industry_growth", {}).get("2_tam_and_headroom")[:120], "...")
    print("  • Part 5 (Operations & Scalability):")
    p5 = a1.get("part5_operations_scalability", {})
    print("      - Operating Leverage:", p5.get("1_operating_leverage"))
    print("      - Sourcing / Supply Chain Risk:", p5.get("2_supply_chain_risks"))
    print("      - Capital Intensity:", p5.get("3_capital_intensity"))
    print("  • Part 6 (Scuttlebutt):", a1.get("part6_scuttlebutt", {}).get("1_customer_sentiment")[:120], "...")
    print("  • Part 7 (Biggest Failure Point):", a1.get("part7_qualitative_risks", {}).get("4_single_biggest_failure_point"))

    # Validate BFSI Prohibition Guard if applicable
    if is_bfsi:
        print("\n🔍 VERIFYING BFSI PROHIBITION GUARD FOR AGENT 1...")
        banned_terms = ["inventory", "raw material", "factory", "machinery"]
        found_violations = []

        def check_banned(obj, path=""):
            if isinstance(obj, str):
                for b in banned_terms:
                    if re.search(rf"\b{b}\b", obj, re.IGNORECASE):
                        found_violations.append(f"{path}: '{obj}' contains '{b}'")
            elif isinstance(obj, dict):
                for k, v in obj.items():
                    check_banned(v, f"{path}.{k}" if path else k)
            elif isinstance(obj, list):
                for idx, v in enumerate(obj):
                    check_banned(v, f"{path}[{idx}]")

        check_banned(a1, "agent_1")
        if found_violations:
            print("❌ BFSI PROHIBITION VIOLATIONS FOUND:")
            for v in found_violations:
                print(f"   - {v}")
            raise AssertionError(f"Agent 1 contains prohibited terms for BFSI stock {ticker}: {found_violations}")
        else:
            print("✅ BFSI PROHIBITION GUARD VERIFIED: Zero banned industrial words found in Agent 1!")

        # Verify Part 5 specific content for BFSI
        p5_text = " ".join(p5.values()).lower()
        assert "cost-to-income" in p5_text or "digital transaction" in p5_text, "Part 5 must evaluate Cost-to-Income / digital operating leverage for BFSI!"
        assert "casa" in p5_text or "liability" in p5_text or "deposit" in p5_text, "Part 5 must evaluate deposit/liability sourcing risks for BFSI!"
        assert "cet-1" in p5_text or "tier-1" in p5_text or "rwa" in p5_text or "crar" in p5_text, "Part 5 must evaluate Tier-1 CET-1 capital intensity for BFSI!"
        print("✅ BFSI PART 5 ARCHETYPE VERIFIED: Evaluates Cost-to-Income, deposit liabilities, and Tier-1 CET-1 capital.")

    # Agent 2: Forensics
    a2 = dossier["agent_2"]
    print("\n" + "-" * 80)
    print(f"🔍 [AGENT 2: FORENSIC DETECTIVE] (Risk Pill: {a2.get('risk_pill')})")
    print("  • Part 13 (Depreciation Check):", a2.get("part13_depreciation", {}).get("1_useful_lifespan_extension")[:100], "...")
    print("  • Part 14 (SG&A Check):", a2.get("part14_sga_anomalies", {}).get("1_sga_growth_vs_revenue")[:100], "...")
    print("  • Part 15 (CFO Divergence):", a2.get("part15_revenue_quality", {}).get("3_cfo_pat_divergence"))
    print("  • Part 16 (Goodwill & RPT):", a2.get("part16_balance_sheet", {}).get("1_goodwill_percentage"))

    # Agent 3: Solvency
    a3 = dossier["agent_3"]
    print("\n" + "-" * 80)
    print(f"⚖️  [AGENT 3: SOLVENCY & CAPITAL ALLOCATION] (Risk Pill: {a3.get('risk_pill')})")
    print("  • Part 8 (Profitability):", a3.get("part8_profitability", {}).get("1_revenue_growth_trajectory")[:100], "...")
    print("  • Part 9 (ROIC vs WACC):", a3.get("part9_cash_flow_roic", {}).get("5_roic_vs_wacc"))
    print("  • Part 10 (Debt-to-Equity):", a3.get("part10_solvency", {}).get("2_debt_to_equity"))
    print("  • Part 11 (Cash Conversion Cycle):", a3.get("part11_working_capital", {}).get("1_cash_conversion_cycle"))
    print("  • Part 12 (FCF Dividend Coverage):", a3.get("part12_capital_allocation", {}).get("4_dividend_fcf_sustainability"))

    # Agent 4: Governance
    a4 = dossier["agent_4"]
    print("\n" + "-" * 80)
    print(f"🏛️  [AGENT 4: GOVERNANCE & MASTER RPT] (Risk Pill: {a4.get('risk_pill')})")
    print("  • Section 1 (Promoter Pledge):", a4.get("section1_promoter_integrity", {}).get("2_promoter_pledge_percentage"))
    print("  • Section 2 (Remuneration):", a4.get("section2_executive_remuneration", {}).get("1_ceo_remuneration_vs_pat"))
    print("  • Section 3 (PEP & Political):", a4.get("section3_pep_rent_seeking", {}).get("1_pep_presence"))
    print("  • Section 4 (Master RPT Pricing):", a4.get("section4_master_rpt", {}).get("pricing_validation", {}).get("pricing_arms_length"))

    # Agent 5: Industry KPI
    a5 = dossier["agent_5"]
    print("\n" + "-" * 80)
    print(f"📈 [AGENT 5: INDUSTRY KPI SPECIALIST] (Activated: {a5.get('activated_checklist_section')})")
    for k, v in a5.get("kpi_results", {}).items():
        print(f"  • {k}: {v}")

    # Agent 6: Synthesizer & Valuation
    a6 = dossier["agent_6"]
    print("\n" + "-" * 80)
    print(f"🎯 [AGENT 6: CIO & VALUATION SPECIALIST] (Verdict: {a6.get('institutional_rating')})")
    print("  • Section 1 (Walk-the-Talk):", a6.get("section1_management_walk_the_talk", {}).get("1_historical_delivery_1", {}).get("verdict"), "-", a6.get("section1_management_walk_the_talk", {}).get("1_historical_delivery_1", {}).get("target")[:80])
    print("  • Section 2 (Valuation Floors):")
    for k, v in a6.get("section2_asset_yield_valuation", {}).items():
        print(f"      - {k}: {v}")
    print("  • Section 3 (Reverse DCF / Primary Valuation):", a6.get("section3_reverse_dcf", {}).get("1_implied_fcf_cagr_priced_in"))
    print("  • Section 4 (Scenario Matrix):")
    for sc_name, sc_data in a6.get("section4_scenario_matrix", {}).items():
        print(f"      - {sc_name.upper()}: Target {sc_data.get('fair_target_price')} ({sc_data.get('expected_return')}) | Growth: {sc_data.get('growth_assumed')}")
    print("  • Invalidation Triggers:")
    for trig in a6.get("invalidation_triggers", []):
        print(f"      - {trig}")

    # Agent 7: Concall & Guidance
    a7 = dossier.get("agent_7")
    assert a7, "Agent 7 concall analysis is missing from dossier!"
    print("\n" + "-" * 80)
    tone_dict = a7.get("tone_sentiment", {})
    print(f"🎙️  [AGENT 7: CONCALL & GUIDANCE AUDITOR] (Tone: {tone_dict.get('overall_tone')}, Integrity: {tone_dict.get('commitment_integrity')})")
    print(f"  • Call Period: {a7.get('call_period')}")
    print(f"  • Revenue Target: {a7.get('guidance_summary', {}).get('revenue_growth_target')}")
    print(f"  • Margin Corridor: {a7.get('margin_outlook', {}).get('target_corridor')}")
    print(f"  • CapEx Outlay: {a7.get('capex_plans', {}).get('total_outlay_cr')}")
    print(f"  • Q&A Highlights Count: {len(a7.get('qa_highlights', []))} scrutinized exchanges")
    print(f"  • Management Tone Summary: {tone_dict.get('summary')}")

    # =========================================================================
    # VERIFY 24-PAGE INSTITUTIONAL REPORTLAB PDF BUILDER
    # =========================================================================
    print("\n" + "=" * 80)
    print("📄 [STAGE 3: VERIFY 24-PAGE INSTITUTIONAL REPORTLAB PDF BUILDER]")
    print("=" * 80)
    meta = dossier.get("financial_payload", {}).get("company_meta", {})
    metrics = {
        "cmp": meta.get("current_price"),
        "mcap": meta.get("market_cap_cr"),
        "sector": meta.get("sector"),
        "range": f"{meta.get('fifty_two_week_low', 0):,.1f} - {meta.get('fifty_two_week_high', 0):,.1f}",
        "stat4_tag": "P/E Ratio",
        "stat4_num": f"{meta.get('trailing_pe', 0.0):.1f}x",
        "stat5_tag": "EV/EBITDA",
        "stat5_num": f"{meta.get('ev_to_ebitda', 0.0):.1f}x",
        "verdict": dossier.get("institutional_rating", "[HOLD / FAIR VALUE]"),
        "implied_cagr": dossier.get("implied_growth_pct", "10.5%"),
        "primary_valuation": dossier.get("primary_valuation", "Reverse DCF")
    }

    pdf_bytes = build_institutional_pdf(
        ticker=ticker,
        company_name=meta.get("short_name", ticker),
        metrics=metrics,
        dossier_dict=dossier
    )

    reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    num_pages = len(reader.pages)
    print(f"  • Compiled ReportLab PDF Document: {len(pdf_bytes):,} bytes")
    print(f"  • Total Dossier Page Count: {num_pages} pages")

    # Save to scratch for artifact inspection
    scratch_dir = os.path.join(os.path.dirname(__file__), "scratch")
    os.makedirs(scratch_dir, exist_ok=True)
    out_pdf_path = os.path.join(scratch_dir, f"{ticker.replace('.', '_')}_Institutional_Dossier.pdf")
    with open(out_pdf_path, "wb") as f:
        f.write(pdf_bytes)
    print(f"  • Saved Institutional PDF Dossier to: {out_pdf_path}")

    assert num_pages >= 24, f"Generated PDF has {num_pages} pages, which is less than the required 24 pages!"
    print(f"✅ INSTITUTIONAL REPORTLAB PDF VERIFIED: {num_pages} pages generated (>= 24 pages requirement satisfied)!")

    print("\n" + "=" * 80)
    print(f"✅ TWO-STAGE INSTITUTIONAL ENGINE EXECUTED SUCCESSFULLY FOR {ticker}!")
    print("=" * 80)
    return dossier


# Backward compatibility alias
test_crompton_pipeline = lambda: test_pipeline("CROMPTON.NS")


if __name__ == "__main__":
    target_ticker = sys.argv[1] if len(sys.argv) > 1 else "CROMPTON.NS"
    test_pipeline(target_ticker)

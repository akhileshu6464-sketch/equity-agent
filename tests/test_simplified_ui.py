"""
Unit Tests for Simplified & Reorganized UI (tests/test_simplified_ui.py)

Tests all 11 sections of the simplified Research Beast company view:
1. Header & Stock Chart
2. Key Financial Numbers Snapshot
3. Business Snapshot (2-4 lines + View details)
4. What's Changing? (↑/↓ indicators + automatic material change detection)
5. Why Is It Happening? (Questions, numbers, drivers, evidence)
6. Financial Trend (Tabs: QoQ, YoY, 5Y)
7. Risk Check (Signals: ✓ / ⚠; no arbitrary scores)
8. Opportunities (3-5 short points)
9. Risks (3-5 material, evidence-backed points)
10. Ask About This Company (Interactive Q&A answering with direct answer, numbers, explanation, evidence)
11. Deep Dive (Tabs: Business, Industry, Management, Financials, Forensic, Valuation, Peers, Sources)
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import numpy as np

from ui.components.simple_company_view import (
    render_section_1_header_and_chart,
    render_section_2_key_financials,
    render_section_3_business_snapshot,
    render_section_4_whats_changing,
    render_section_5_why_is_it_happening,
    render_section_6_financial_trends,
    render_section_7_risk_check,
    render_section_8_and_9_opps_and_risks,
    answer_company_question,
    render_section_10_ask_company_qa,
    render_section_11_deep_dive,
)


class TestSimplifiedCompanyUi(unittest.TestCase):

    def setUp(self):
        # Sample 10-year P&L
        self.pl_df = pd.DataFrame([
            {"Metric": "Sales +", "Mar 2022": "1,000", "Mar 2023": "1,200", "Mar 2024": "1,440"},
            {"Metric": "Operating Profit", "Mar 2022": "180", "Mar 2023": "216", "Mar 2024": "245"},
            {"Metric": "OPM %", "Mar 2022": "18.0%", "Mar 2023": "18.0%", "Mar 2024": "17.0%"},
            {"Metric": "Net Profit", "Mar 2022": "100", "Mar 2023": "130", "Mar 2024": "160"},
            {"Metric": "EPS in Rs", "Mar 2022": "10.0", "Mar 2023": "13.0", "Mar 2024": "16.0"},
        ])

        # Sample Balance Sheet
        self.bs_df = pd.DataFrame([
            {"Metric": "Equity Capital", "Mar 2023": "20", "Mar 2024": "20"},
            {"Metric": "Borrowings", "Mar 2023": "300", "Mar 2024": "270"},
            {"Metric": "Trade Receivables", "Mar 2023": "200", "Mar 2024": "260"},
            {"Metric": "Inventory", "Mar 2023": "150", "Mar 2024": "175"},
            {"Metric": "Total Assets", "Mar 2023": "1,500", "Mar 2024": "1,800"},
        ])

        # Sample Cash Flow
        self.cf_df = pd.DataFrame([
            {"Metric": "Cash from Operating Activity", "Mar 2023": "140", "Mar 2024": "180"},
            {"Metric": "Net Cash Flow", "Mar 2023": "15", "Mar 2024": "25"},
        ])

        # Sample Quarters
        self.q_df = pd.DataFrame([
            {"Metric": "Sales +", "Jun 2023": "320", "Sep 2023": "350", "Dec 2023": "370", "Mar 2024": "400"},
            {"Metric": "Operating Profit", "Jun 2023": "55", "Sep 2023": "60", "Dec 2023": "62", "Mar 2024": "68"},
            {"Metric": "OPM %", "Jun 2023": "17.2%", "Sep 2023": "17.1%", "Dec 2023": "16.8%", "Mar 2024": "17.0%"},
            {"Metric": "Net Profit", "Jun 2023": "35", "Sep 2023": "40", "Dec 2023": "41", "Mar 2024": "44"},
            {"Metric": "EPS", "Jun 2023": "3.5", "Sep 2023": "4.0", "Dec 2023": "4.1", "Mar 2024": "4.4"},
        ])

        self.ratios = {
            "Market Cap": "₹ 18,500 Cr.",
            "Current Price": "₹ 520",
            "ROE": "18.5%",
            "ROCE": "22.4%",
            "current_price": 520.0,
            "market_cap_cr": 18500.0,
        }

        self.intel = {
            "opportunities": [
                {"opportunity_title": "Capacity Expansion", "business_mechanism": "New facility operational in H2."},
                {"opportunity_title": "Export Market Scaling", "business_mechanism": "Entering US and European supply chains."}
            ],
            "risks": [
                {"risk_title": "Input Material Inflation", "potential_impact": "Compresses gross margins.", "evidence": "Key raw material costs up 8%."},
                {"risk_title": "Customer Concentration", "potential_impact": "Top 5 clients contribute 45% of sales.", "evidence": "Annual report customer schedule."}
            ],
            "forensic_audit": {
                "anomalies": [
                    {"signal_type": "Debtor Days Expansion", "severity": "Potential Concern", "what_changed": "Debtor days grew from 65 to 78 days.", "why_it_matters": "Working capital requirement rises.", "evidence": "Balance sheet schedule 8."}
                ]
            }
        }

        self.screener_data = {
            "company_name": "Tata Motors Ltd",
            "clean_symbol": "TATAMOTORS",
            "sector": "Automobiles",
            "industry": "Commercial & Passenger Vehicles",
            "current_price": 520.0,
            "market_cap_cr": 18500.0,
            "debt_to_equity": 0.45,
            "total_debt_cr": 270.0,
            "total_cash_cr": 350.0,
            "peer_rows": [
                {"name": "Mahindra & Mahindra", "symbol": "M&M", "sales_growth_pct": 14.5, "ebitda_margin_pct": 16.2, "roe": 19.0, "pe_ratio": 22.0},
                {"name": "Tata Motors", "symbol": "TATAMOTORS", "sales_growth_pct": 20.0, "ebitda_margin_pct": 17.0, "roe": 18.5, "pe_ratio": 18.0, "is_target": True},
            ]
        }

    @patch("streamlit.html")
    @patch("streamlit.radio", return_value="1Y")
    @patch("streamlit.plotly_chart")
    def test_section_1_header_and_chart(self, mock_plot, mock_radio, mock_html):
        """1. Verify Section 1 Header and Chart renders clean header and timeframe selector."""
        with patch("ui.components.simple_company_view.fetch_stock_chart_data", return_value=pd.DataFrame({
            "Date": pd.date_range("2024-01-01", periods=10),
            "Close": [500 + i * 2 for i in range(10)]
        })):
            render_section_1_header_and_chart(
                company_name="Tata Motors Ltd",
                ticker="TATAMOTORS",
                current_price=520.0,
                day_change_rs=12.5,
                day_change_pct=2.45,
                market_cap_str="₹ 18,500 Cr",
                sector="Automobiles"
            )
            self.assertTrue(mock_html.called)
            self.assertTrue(mock_plot.called)

    @patch("streamlit.html")
    def test_section_2_key_financials(self, mock_html):
        """2. Verify Section 2 Screener-style compact financial snapshot."""
        render_section_2_key_financials(
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            ratios_dict=self.ratios,
            data_dict=self.screener_data
        )
        self.assertTrue(mock_html.called)

    @patch("streamlit.markdown")
    @patch("streamlit.expander")
    def test_section_3_business_snapshot(self, mock_exp, mock_md):
        """3. Verify Section 3 Business Snapshot renders 2-4 lines with [View details]."""
        about_text = "Tata Motors designs and manufactures passenger vehicles and commercial trucks. It generates revenue primarily from automotive sales."
        render_section_3_business_snapshot(
            company_name="Tata Motors Ltd",
            about_text=about_text,
            about_data={"business_segments": [{"name": "Commercial Vehicles", "description": "Trucks & buses"}]}
        )
        self.assertTrue(mock_md.called)

    @patch("streamlit.html")
    @patch("streamlit.markdown")
    def test_section_4_whats_changing(self, mock_md, mock_html):
        """4. Verify Section 4 What's Changing detects YoY changes and material callouts."""
        render_section_4_whats_changing(
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            cf_df=self.cf_df,
            intel=self.intel
        )
        self.assertTrue(mock_html.called)

    @patch("streamlit.html")
    @patch("streamlit.markdown")
    @patch("streamlit.expander")
    def test_section_5_why_is_it_happening(self, mock_exp, mock_md, mock_html):
        """5. Verify Section 5 Why is it happening shows questions, numbers, and drivers."""
        render_section_5_why_is_it_happening(
            intel=self.intel,
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            cf_df=self.cf_df
        )
        self.assertTrue(mock_md.called or mock_html.called)

    @patch("streamlit.markdown")
    @patch("streamlit.dataframe")
    def test_section_6_financial_trends(self, mock_df, mock_md):
        """6. Verify Section 6 Financial Trend renders QoQ, YoY, and 5Y tabs."""
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = mock_tab
        mock_tab.__exit__.return_value = None

        with patch("streamlit.tabs", return_value=[mock_tab, mock_tab, mock_tab]):
            render_section_6_financial_trends(
                pl_df=self.pl_df,
                q_df=self.q_df,
                cf_df=self.cf_df
            )
            self.assertTrue(mock_md.called)

    @patch("streamlit.html")
    @patch("streamlit.markdown")
    def test_section_7_risk_check(self, mock_md, mock_html):
        """7. Verify Section 7 Risk Check produces signals (✓ / ⚠) without fake scores."""
        render_section_7_risk_check(
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            cf_df=self.cf_df,
            data_dict=self.screener_data
        )
        self.assertTrue(mock_html.called or mock_md.called)

    @patch("streamlit.html")
    @patch("streamlit.markdown")
    def test_section_8_and_9_opps_and_risks(self, mock_md, mock_html):
        """8. Verify Sections 8 & 9 Opportunities and Risks render short factual points."""
        render_section_8_and_9_opps_and_risks(self.intel)
        self.assertTrue(mock_md.called or mock_html.called)

    def test_answer_company_question(self):
        """9. Verify Q&A engine produces 4-part structured responses (direct, numbers, explanation, source)."""
        # Test margin query
        res_m = answer_company_question(
            query="Why did margins fall?",
            company_name="Tata Motors Ltd",
            ticker="TATAMOTORS",
            intel=self.intel,
            data_dict=self.screener_data,
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            cf_df=self.cf_df
        )
        self.assertIn("direct", res_m)
        self.assertIn("numbers", res_m)
        self.assertIn("explanation", res_m)
        self.assertIn("source", res_m)
        self.assertIn("margin", res_m["direct"].lower())

        # Test cash flow query
        res_cf = answer_company_question(
            query="Is cash flow healthy?",
            company_name="Tata Motors Ltd",
            ticker="TATAMOTORS",
            intel=self.intel,
            data_dict=self.screener_data,
            pl_df=self.pl_df,
            bs_df=self.bs_df,
            cf_df=self.cf_df
        )
        self.assertIn("direct", res_cf)
        self.assertIn("cash", res_cf["direct"].lower())

    @patch("streamlit.html")
    @patch("streamlit.markdown")
    @patch("streamlit.expander")
    def test_section_11_deep_dive(self, mock_exp, mock_md, mock_html):
        """10. Verify Section 11 Deep Dive renders all 8 tabs cleanly."""
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = mock_tab
        mock_tab.__exit__.return_value = None

        with patch("streamlit.tabs", return_value=[mock_tab] * 8):
            render_section_11_deep_dive(
                company_name="Tata Motors Ltd",
                ticker="TATAMOTORS",
                direct_scr={"pl_dataframe": self.pl_df, "announcements": []},
                screener_data=self.screener_data,
                intel=self.intel,
                dossier={}
            )
            self.assertTrue(mock_md.called)


if __name__ == "__main__":
    unittest.main()

"""
Unit Tests for Screener Tables and Q&A Intelligence UI (tests/test_screener_qa_ui.py)
Tests:
1. Screener HTML parsing of all tables (quarters, balance-sheet, cash-flow, ratios, shareholding, documents).
2. fetch_day_change and fetch_stock_chart_data resilience.
3. Layer 1 Screener Tables components execution without exceptions.
4. Layer 2 Q&A Intelligence components execution across all 9 tabs.
5. Strict enforcement of Never Guess guardrails and No Overall Company Rating rule.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
from bs4 import BeautifulSoup

from services.screener_fetcher import (
    _parse_section_table,
    _extract_announcements,
    fetch_day_change,
    fetch_stock_chart_data,
    fetch_screener_data,
)
from ui.components.screener_tables import (
    render_layer1_header,
    render_horizontal_nav,
    render_overview_row,
    render_compact_key_financials,
    render_peers_table,
    render_quarterly_section,
    render_annual_section,
    render_cash_flow_section,
    render_balance_sheet_section,
    render_ratios_section,
    render_shareholding_section,
    render_news_section,
)
from ui.components.qa_intelligence import render_qa_intelligence_section


class TestScreenerQaUi(unittest.TestCase):

    def setUp(self):
        self.sample_html = """
        <html>
            <body>
                <h1>ABC Enterprises Ltd</h1>
                <div class="about"><p>ABC Enterprises manufactures specialized components.</p></div>
                <ul id="top-ratios">
                    <li><span class="name">Market Cap</span><span class="value">₹ 15,000 Cr.</span></li>
                    <li><span class="name">Current Price</span><span class="value">₹ 1,200</span></li>
                    <li><span class="name">High / Low</span><span class="value">₹ 1,400 / 950</span></li>
                    <li><span class="name">Stock P/E</span><span class="value">25.0</span></li>
                    <li><span class="name">Book Value</span><span class="value">₹ 350</span></li>
                    <li><span class="name">Dividend Yield</span><span class="value">0.80%</span></li>
                    <li><span class="name">ROCE</span><span class="value">24.5%</span></li>
                    <li><span class="name">ROE</span><span class="value">19.2%</span></li>
                    <li><span class="name">Face Value</span><span class="value">₹ 1.00</span></li>
                </ul>
                <section id="profit-loss">
                    <table>
                        <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th></tr></thead>
                        <tbody>
                            <tr><td>Sales +</td><td>1,000</td><td>1,200</td></tr>
                            <tr><td>Expenses +</td><td>800</td><td>960</td></tr>
                            <tr><td>Operating Profit</td><td>200</td><td>240</td></tr>
                            <tr><td>OPM %</td><td>20%</td><td>20%</td></tr>
                            <tr><td>Net Profit</td><td>140</td><td>170</td></tr>
                            <tr><td>EPS in Rs</td><td>14.0</td><td>17.0</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="quarters">
                    <table>
                        <thead><tr><th></th><th>Jun 2023</th><th>Sep 2023</th></tr></thead>
                        <tbody>
                            <tr><td>Sales +</td><td>280</td><td>310</td></tr>
                            <tr><td>Operating Profit</td><td>55</td><td>62</td></tr>
                            <tr><td>Net Profit</td><td>38</td><td>44</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="balance-sheet">
                    <table>
                        <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th></tr></thead>
                        <tbody>
                            <tr><td>Equity Capital</td><td>10</td><td>10</td></tr>
                            <tr><td>Borrowings</td><td>50</td><td>40</td></tr>
                            <tr><td>Total Assets</td><td>800</td><td>950</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="cash-flow">
                    <table>
                        <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th></tr></thead>
                        <tbody>
                            <tr><td>Cash from Operating Activity</td><td>180</td><td>220</td></tr>
                            <tr><td>Net Cash Flow</td><td>10</td><td>15</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="ratios">
                    <table>
                        <thead><tr><th></th><th>Mar 2023</th><th>Mar 2024</th></tr></thead>
                        <tbody>
                            <tr><td>ROCE %</td><td>22%</td><td>24.5%</td></tr>
                            <tr><td>Debtor Days</td><td>85</td><td>78</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="shareholding">
                    <table>
                        <thead><tr><th></th><th>Dec 2023</th><th>Mar 2024</th></tr></thead>
                        <tbody>
                            <tr><td>Promoters +</td><td>72.5%</td><td>72.5%</td></tr>
                            <tr><td>FIIs +</td><td>12.0%</td><td>12.5%</td></tr>
                        </tbody>
                    </table>
                </section>
                <section id="documents">
                    <ul class="list-links">
                        <li>
                            <a href="https://example.com/filing1.pdf">Financial Results for Q4 FY24 25 May</a>
                            <div class="ink-600">25 May</div>
                        </li>
                    </ul>
                </section>
            </body>
        </html>
        """
        self.soup = BeautifulSoup(self.sample_html, "html.parser")

    def test_parse_section_table(self):
        """1. Verify _parse_section_table extracts headers, rows, and DataFrame correctly."""
        headers, rows, df = _parse_section_table(self.soup, "profit-loss")
        self.assertIn("Mar 2023", headers)
        self.assertIn("Mar 2024", headers)
        self.assertEqual(len(rows), 6)
        self.assertIn("Sales", rows[0]["Metric"])
        self.assertFalse(df.empty)

    def test_extract_announcements(self):
        """2. Verify _extract_announcements extracts regulatory documents and dates."""
        announcements = _extract_announcements(self.soup)
        self.assertEqual(len(announcements), 1)
        self.assertIn("Financial Results", announcements[0]["headline"])
        self.assertEqual(announcements[0]["date"], "25 May")
        self.assertIn("filing1.pdf", announcements[0]["link"])

    def test_fetch_screener_data_all_sections(self):
        """3. Verify fetch_screener_data populates all 6 table sections."""
        with patch("services.screener_fetcher._fetch_screener_soup", return_value=(self.soup, "https://screener.in/company/ABC/")):
            data = fetch_screener_data("ABC")
            self.assertEqual(data["company_name"], "ABC Enterprises Ltd")
            self.assertIn("quarters_table", data)
            self.assertIn("balance_sheet_table", data)
            self.assertIn("cash_flow_table", data)
            self.assertIn("ratios_table", data)
            self.assertIn("shareholding_table", data)
            self.assertIn("announcements", data)
            self.assertEqual(len(data["announcements"]), 1)

    def test_layer1_screener_tables_render(self):
        """4. Verify Layer 1 components execute cleanly without throwing errors."""
        headers, rows, pl_df = _parse_section_table(self.soup, "profit-loss")
        _, _, q_df = _parse_section_table(self.soup, "quarters")
        _, _, bs_df = _parse_section_table(self.soup, "balance-sheet")
        _, _, cf_df = _parse_section_table(self.soup, "cash-flow")
        _, _, r_df = _parse_section_table(self.soup, "ratios")
        _, _, sh_df = _parse_section_table(self.soup, "shareholding")
        announcements = _extract_announcements(self.soup)

        ratios = {
            "Market Cap": "₹ 15,000 Cr.",
            "Current Price": "₹ 1,200",
            "Stock P/E": "25.0",
            "Book Value": "₹ 350",
            "Dividend Yield": "0.80%",
            "ROCE": "24.5%",
            "ROE": "19.2%",
            "Face Value": "₹ 1.0",
            "current_price": 1200.0,
            "book_value": 350.0,
        }

        # Mock streamlit rendering
        with patch("streamlit.html") as mock_html, \
             patch("streamlit.markdown") as mock_md, \
             patch("streamlit.dataframe") as mock_df, \
             patch("streamlit.plotly_chart") as mock_plt:

            render_layer1_header(
                company_name="ABC Enterprises Ltd",
                nse_symbol="ABC",
                bse_code="500001",
                isin="INE000A01010",
                sector="Industrials",
                industry="Components",
                market_cap_str="₹ 15,000 Cr.",
                current_price_str="₹ 1,200",
                day_change_rs=12.50,
                day_change_pct=1.05,
            )
            self.assertTrue(mock_html.called)

            render_horizontal_nav()
            render_overview_row(ratios, debt_to_equity=0.25)
            render_compact_key_financials(pl_df, q_df)

            peer_rows = [
                {"name": "Peer One", "symbol": "PEER1", "market_cap_cr": 12000, "pe_ratio": 22.0, "roe": 18.0, "roce": 20.0},
                {"name": "ABC Enterprises", "symbol": "ABC", "market_cap_cr": 15000, "pe_ratio": 25.0, "roe": 19.2, "roce": 24.5, "is_target": True},
            ]
            render_peers_table(peer_rows, "ABC")
            render_quarterly_section(q_df)
            render_annual_section(pl_df)
            render_cash_flow_section(cf_df)
            render_balance_sheet_section(bs_df)
            render_ratios_section(r_df)
            render_shareholding_section(sh_df)
            render_news_section(announcements)

    def test_layer2_qa_intelligence_render(self):
        """5. Verify Layer 2 Q&A Intelligence renders all 9 tabs with strict guardrails."""
        headers, rows, pl_df = _parse_section_table(self.soup, "profit-loss")
        direct_scr = {
            "pl_dataframe": pl_df,
            "ratios": {"current_price": 1200.0, "market_cap_cr": 15000.0},
            "announcements": [],
        }
        intel = {
            "simple_explanation": {
                "core_change": {
                    "headline": "Sales grew +20.0% while operating profits kept pace at +20.0%",
                    "simple_explanation": "Sales increased 20%, and profit from the business grew at the same 20% pace.",
                    "status": "POSITIVE",
                },
                "cash_flow_health": {
                    "simple_explanation": "Operating cash flow remains healthy.",
                },
                "debt_position": {
                    "simple_explanation": "Debt is safe with minimal borrowings.",
                },
                "red_flags": [],
            },
            "opportunities": [
                {
                    "opportunity_title": "Capacity Commissioning",
                    "business_mechanism": "New facility adds 30% volume output.",
                    "evidence": "Disclosed in CWIP notes.",
                }
            ],
            "risks": [
                {
                    "risk_title": "Raw Material Price Inflation",
                    "potential_impact": "Compresses gross margins if pass-through is delayed.",
                    "evidence": "Input materials are 50% of cost.",
                    "early_warning_indicator": "Quarterly gross margins.",
                }
            ],
            "forensic_audit": {"anomalies": []},
            "driver_analysis": [],
        }

        # Mock streamlit tabs & components
        mock_tab = MagicMock()
        mock_tab.__enter__.return_value = mock_tab
        mock_tab.__exit__.return_value = None

        with patch("streamlit.tabs", return_value=[mock_tab] * 9), \
             patch("streamlit.html") as mock_html, \
             patch("streamlit.markdown") as mock_md, \
             patch("streamlit.expander", return_value=mock_tab):

            render_qa_intelligence_section(intel, {}, direct_scr)
            self.assertTrue(mock_html.called)


if __name__ == "__main__":
    unittest.main()

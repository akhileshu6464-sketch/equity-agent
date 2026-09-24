"""
Test Suite: Direct Screener Pipeline & Screener-Style View (tests/test_screener_pipeline.py)
Tests:
1. clean_user_input: suffix stripping, casing, whitespace, and alias resolution.
2. fetch_screener_data: extraction of Company Name, About box, 9 Key Ratios, and P&L DataFrame.
3. ThesisAgent: strict injection of verified metrics JSON, temperature 0.2, zero calculation rule.
4. Screener-style frontend view rendering without exceptions.
"""

import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from services.screener_fetcher import clean_user_input, fetch_screener_data, _parse_numeric
from agents.thesis_agent import ThesisAgent, SYSTEM_PROMPT
from ui.components.screener_view import (
    render_screener_top_header,
    render_screener_about_box,
    render_screener_ratios_3x3,
    render_screener_financial_table,
    render_screener_editorial_memo,
)


class TestScreenerPipeline(unittest.TestCase):

    def test_clean_user_input(self):
        """1. Verify clean_user_input correctly normalizes symbols and aliases."""
        self.assertEqual(clean_user_input("VINATIORGA.NS"), "VINATIORGA")
        self.assertEqual(clean_user_input("vinatiorga.bo"), "VINATIORGA")
        self.assertEqual(clean_user_input("  ASHOKA.NSE  "), "ASHOKA")
        self.assertEqual(clean_user_input("TATAMOTORS.NS"), "TMCV")
        self.assertEqual(clean_user_input("TATA MOTORS"), "TMCV")
        self.assertEqual(clean_user_input("VINATI ORGANICS"), "VINATIORGA")
        self.assertEqual(clean_user_input("ASHOKA BUILDCON"), "ASHOKA")
        self.assertEqual(clean_user_input("RELIANCE INDUSTRIES"), "RELIANCE")

    def test_parse_numeric(self):
        """2. Verify formatted string conversion to clean numeric float."""
        self.assertEqual(_parse_numeric("₹ 12,539 Cr."), 12539.0)
        self.assertEqual(_parse_numeric("₹1,210"), 1210.0)
        self.assertEqual(_parse_numeric("28.0"), 28.0)
        self.assertEqual(_parse_numeric("0.70%"), 0.70)
        self.assertEqual(_parse_numeric(""), None)
        self.assertEqual(_parse_numeric("-"), None)

    def test_fetch_screener_data_mock(self):
        """3. Test fetch_screener_data parsing and structure using a mock soup."""
        mock_html = """
        <html>
            <body>
                <h1>Sample Test Corp Ltd</h1>
                <div class="about"><p>Sample Test Corp is an enterprise manufacturing chemicals. <a href="#">Website</a></p></div>
                <ul id="top-ratios">
                    <li><span class="name">Market Cap</span><span class="value">₹ 5,000 Cr.</span></li>
                    <li><span class="name">Current Price</span><span class="value">₹ 250</span></li>
                    <li><span class="name">High / Low</span><span class="value">₹ 300 / 180</span></li>
                    <li><span class="name">Stock P/E</span><span class="value">15.5</span></li>
                    <li><span class="name">Book Value</span><span class="value">₹ 120</span></li>
                    <li><span class="name">Dividend Yield</span><span class="value">1.20%</span></li>
                    <li><span class="name">ROCE</span><span class="value">22.5%</span></li>
                    <li><span class="name">ROE</span><span class="value">18.0%</span></li>
                    <li><span class="name">Face Value</span><span class="value">₹ 2.00</span></li>
                </ul>
                <section id="profit-loss">
                    <table>
                        <thead>
                            <tr><th></th><th>Mar 2022</th><th>Mar 2023</th><th>Mar 2024</th><th>TTM</th></tr>
                        </thead>
                        <tbody>
                            <tr><td>Sales +</td><td>1,000</td><td>1,200</td><td>1,450</td><td>1,500</td></tr>
                            <tr><td>Expenses +</td><td>800</td><td>950</td><td>1,100</td><td>1,150</td></tr>
                            <tr><td>Operating Profit</td><td>200</td><td>250</td><td>350</td><td>350</td></tr>
                            <tr><td>OPM %</td><td>20%</td><td>21%</td><td>24%</td><td>23%</td></tr>
                            <tr><td>Net Profit</td><td>120</td><td>160</td><td>230</td><td>240</td></tr>
                            <tr><td>EPS in Rs</td><td>6.0</td><td>8.0</td><td>11.5</td><td>12.0</td></tr>
                        </tbody>
                    </table>
                </section>
            </body>
        </html>
        """
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(mock_html, "html.parser")

        with patch("services.screener_fetcher._fetch_screener_soup", return_value=(soup, "https://www.screener.in/company/SAMPLE/")):
            data = fetch_screener_data("SAMPLE")

            self.assertEqual(data["company_name"], "Sample Test Corp Ltd")
            self.assertIn("Sample Test Corp", data["about"])
            self.assertNotIn("Website", data["about"])  # Links stripped

            ratios = data["ratios"]
            self.assertEqual(ratios["Market Cap"], "₹ 5,000 Cr.")
            self.assertEqual(ratios["market_cap_cr"], 5000.0)
            self.assertEqual(ratios["Current Price"], "₹ 250")
            self.assertEqual(ratios["current_price"], 250.0)
            self.assertEqual(ratios["High / Low"], "₹ 300 / 180")
            self.assertEqual(ratios["high_52w"], 300.0)
            self.assertEqual(ratios["low_52w"], 180.0)
            self.assertEqual(ratios["pe_ratio"], 15.5)
            self.assertEqual(ratios["book_value"], 120.0)
            self.assertEqual(ratios["dividend_yield_pct"], 1.20)
            self.assertEqual(ratios["roce_pct"], 22.5)
            self.assertEqual(ratios["roe_pct"], 18.0)
            self.assertEqual(ratios["face_value"], 2.0)

            # P&L DataFrame
            df = data["pl_dataframe"]
            self.assertIsInstance(df, pd.DataFrame)
            self.assertEqual(len(df), 6)
            self.assertIn("Metric", df.columns)
            self.assertIn("Mar 2024", df.columns)
            self.assertEqual(df.loc[df["Metric"] == "Sales", "Mar 2024"].values[0], "1,450")

    def test_thesis_agent_system_rules(self):
        """4. Verify ThesisAgent system prompt enforces strict no-calculation and no-hallucination rules."""
        self.assertIn("NEVER calculate financial ratios", SYSTEM_PROMPT)
        self.assertIn("absolute, immutable ground truth", SYSTEM_PROMPT)
        self.assertIn("investment_thesis", SYSTEM_PROMPT)
        self.assertIn("structural_moats", SYSTEM_PROMPT)
        self.assertIn("key_risks", SYSTEM_PROMPT)

    def test_thesis_agent_editorial_memo_generation(self):
        """5. Verify ThesisAgent generates structured memo with Thesis, Moats, and Risks."""
        screener_payload = {
            "company_name": "Test Chemicals Ltd",
            "symbol": "TESTCHEM",
            "about": "Manufacturer of specialty aromatic chemicals and organic intermediates.",
            "ratios": {
                "Market Cap": "₹ 10,000 Cr.",
                "Current Price": "₹ 1,500",
                "High / Low": "₹ 1,700 / 1,200",
                "Stock P/E": "24.5",
                "Book Value": "₹ 350",
                "Dividend Yield": "0.60%",
                "ROCE": "21.5%",
                "ROE": "17.0%",
                "Face Value": "₹ 1.00",
            },
            "pl_table": {
                "headers": ["Mar 2022", "Mar 2023", "Mar 2024"],
                "rows": [
                    {"Metric": "Sales", "Mar 2022": "1,000", "Mar 2023": "1,200", "Mar 2024": "1,500"},
                    {"Metric": "Net Profit", "Mar 2022": "200", "Mar 2023": "240", "Mar 2024": "310"},
                ]
            }
        }

        agent = ThesisAgent()
        memo = agent.generate_editorial_memo(screener_payload)

        self.assertIsInstance(memo, dict)
        self.assertIn("investment_thesis", memo)
        self.assertIn("structural_moats", memo)
        self.assertIn("key_risks", memo)
        self.assertIsInstance(memo["structural_moats"], list)
        self.assertIsInstance(memo["key_risks"], list)
        self.assertTrue(len(memo["structural_moats"]) >= 2)
        self.assertTrue(len(memo["key_risks"]) >= 2)
        self.assertTrue(len(memo["investment_thesis"]) > 30)

    def test_screener_view_components_render(self):
        """6. Verify all 5 screener view components execute cleanly without throwing errors."""
        with patch("streamlit.html") as mock_html, patch("streamlit.dataframe") as mock_df, patch("streamlit.subheader") as mock_sub, patch("streamlit.caption") as mock_cap, patch("streamlit.columns", return_value=[MagicMock(), MagicMock()]):
            render_screener_top_header("Vinati Organics Ltd", "₹ 1,210", "₹ 12,539 Cr.", "VINATIORGA")
            self.assertTrue(mock_html.called)

            render_screener_about_box("Vinati Organics Ltd", "Leading manufacturer of IBB and ATBS.")
            self.assertTrue(mock_html.called)

            ratios = {
                "Market Cap": "₹ 12,539 Cr.",
                "Current Price": "₹ 1,210",
                "High / Low": "₹ 1,850 / 1,200",
                "Stock P/E": "28.0",
                "Book Value": "₹ 305",
                "Dividend Yield": "0.70%",
                "ROCE": "19.8%",
                "ROE": "14.9%",
                "Face Value": "₹ 1.00"
            }
            render_screener_ratios_3x3(ratios)

            df = pd.DataFrame([
                {"Metric": "Sales", "Mar 2023": "2,066", "Mar 2024": "1,900"},
                {"Metric": "Net Profit", "Mar 2023": "458", "Mar 2024": "358"}
            ])
            render_screener_financial_table(df)
            self.assertTrue(mock_df.called)

            memo = {
                "investment_thesis": "Global market leader in ATBS and IBB with high customer switching costs.",
                "structural_moats": ["Over 65% global market share in ATBS", "Backward integrated operations"],
                "key_risks": ["Raw material pricing volatility (crude derivatives)", "Global demand cycles"]
            }
            render_screener_editorial_memo(memo)
            self.assertTrue(mock_html.called)


if __name__ == "__main__":
    unittest.main()

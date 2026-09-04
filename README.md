# BharatAlpha: 7-Agent Institutional Equity Research Platform (NSE / BSE)

An autonomous, multi-agent fundamental analysis platform for Indian equities. BharatAlpha audits financial statements, forensic accounting flags, solvency, corporate governance, related-party transactions (RPTs), industry KPIs, and reverse discounted cash flow (DCF) hurdle tests.

---

## 🏛️ Multi-Agent Architecture

The engine coordinates seven specialized analytical agents:

| Agent | Module | Prompt Specification | Scope & Checklist |
| :--- | :--- | :--- | :--- |
| **Agent 0** | `agent0_classifier.py` | `agent0_classifier.txt` | 12-sector taxonomy, hybrid verticals, and routing profile JSON |
| **Agent 1** | `agent1_qualitative.py` | `agent1_qualitative.txt` | Business model, economic moat durability, TAM, scalability, scuttlebutt, qualitative risks |
| **Agent 2** | `agent2_forensics.py` | `agent2_forensics.txt` | D&A manipulation, SG&A anomalies, 5-year cumulative CFO/PAT divergence, goodwill risks |
| **Agent 3** | `agent3_solvency.py` | `agent3_solvency.txt` | Balance sheet solvency, normalized ROIC vs WACC, Cash Conversion Cycle (CCC), FCF dividend coverage |
| **Agent 4** | `agent4_governance.py` | `agent4_governance_rpt.txt` | Promoter pledge, executive remuneration vs PAT, PEP risk, Master Related Party Transactions (RPT) matrix |
| **Agent 5** | `agent5_industry_kpi.py` | `agent5_industry_kpi.txt` | Sector-specific operational KPIs (GMROI, inventory velocity, plant capacity utilization) |
| **Agent 6** | `agent6_synthesizer.py` | `agent6_valuation_cio.txt` | Walk-the-Talk audit, valuation floors (TBV, Graham NCAV, EPV), Reverse DCF hurdle test, 3-scenario matrix |

---

## 🚀 Quickstart

### 1. Installation
Clone the repository and install dependencies:
```bash
git clone https://github.com/akhileshu6464-sketch/equity-agent.git
cd equity-agent
pip install -r requirements.txt
```

### 2. Run CLI Pipeline
Analyze any Indian stock ticker directly via command line:
```bash
python pipeline.py CROMPTON.NS
python pipeline.py RELIANCE.NS
python pipeline.py TCS.NS
```

### 3. Launch Streamlit Web Dashboard
Launch the interactive web dashboard with colored risk pills, accordion tabs, and interactive DCF sliders:
```bash
streamlit run app.py
```
Open `http://localhost:8501` in your browser.

---

## 🚦 Risk Pill Dashboard
The platform outputs colored institutional risk badges across six core operational domains:
- 🟢 **Moat & Business Model**
- 🟡 **Forensic Accounting**
- 🟢 **Balance Sheet Solvency**
- 🟢 **Corporate Governance & RPT**
- 🟢 **Industry-Specific KPIs**
- 🟢 **Valuation & Reverse DCF**

---

## 📜 License
MIT License.

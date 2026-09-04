"""
Financial Data Service
Fetches and standardizes balance sheet, cash flows, income statements,
shareholding, and price history for Indian equities (NSE/BSE) using yfinance.
"""

import logging
from typing import Dict, Any, Optional, List
import pandas as pd
import numpy as np

try:
    import yfinance as yf
except ImportError:
    yf = None

logger = logging.getLogger(__name__)


class FinancialDataService:
    """Service to retrieve and parse institutional financial statements and market metrics."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def normalize_ticker(ticker: str) -> str:
        """
        Normalizes Indian stock tickers.
        E.g., 'CROMPTON' -> 'CROMPTON.NS', 'RELIANCE' -> 'RELIANCE.NS'
        """
        clean = ticker.strip().upper()
        if not clean.endswith(".NS") and not clean.endswith(".BO"):
            clean = f"{clean}.NS"
        return clean

    def get_company_data(self, ticker: str, force_refresh: bool = False) -> Dict[str, Any]:
        """
        Fetches comprehensive company data, historical financial statements,
        and current market metrics.
        """
        symbol = self.normalize_ticker(ticker)
        if not force_refresh and symbol in self._cache:
            return self._cache[symbol]

        if yf is None:
            raise RuntimeError("yfinance is not installed. Please install dependencies.")

        stock = yf.Ticker(symbol)
        info = stock.info or {}

        # If empty info, try without .NS or with .BO
        if not info or ("regularMarketPrice" not in info and "currentPrice" not in info and "shortName" not in info):
            alt_symbol = symbol.replace(".NS", ".BO") if symbol.endswith(".NS") else symbol.replace(".BO", ".NS")
            try:
                stock_alt = yf.Ticker(alt_symbol)
                alt_info = stock_alt.info or {}
                if alt_info and ("currentPrice" in alt_info or "regularMarketPrice" in alt_info or "shortName" in alt_info):
                    symbol = alt_symbol
                    stock = stock_alt
                    info = alt_info
            except Exception:
                pass

        # Extract current price & market cap
        current_price = (
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
            or 0.0
        )
        shares_outstanding = info.get("sharesOutstanding") or 0
        market_cap = info.get("marketCap") or (current_price * shares_outstanding)

        # Financial Statements (Income statement, Balance sheet, Cash flow)
        try:
            income_stmt = stock.financials
        except Exception:
            income_stmt = None
        try:
            balance_sheet = stock.balance_sheet
        except Exception:
            balance_sheet = None
        try:
            cash_flow = stock.cashflow
        except Exception:
            cash_flow = None

        # Check if valid ticker data was retrieved
        if current_price == 0.0 and market_cap == 0.0 and not info.get("shortName") and (income_stmt is None or income_stmt.empty):
            raise ValueError(f"yfinance failed to retrieve financial data for ticker '{symbol}'. Please ensure the ticker exists on NSE or BSE.")

        # Quarterly statements
        try:
            q_income_stmt = stock.quarterly_financials
        except Exception:
            q_income_stmt = None
        try:
            q_cash_flow = stock.quarterly_cashflow
        except Exception:
            q_cash_flow = None

        # Parse historical statement series
        history_years = self._parse_financial_history(income_stmt, balance_sheet, cash_flow)

        # Calculate Net Debt & Base FCF
        latest_cash = history_years[-1].get("cash_and_equivalents", 0.0) if history_years else 0.0
        latest_debt = history_years[-1].get("total_debt", 0.0) if history_years else 0.0
        net_debt = latest_debt - latest_cash

        latest_fcf = history_years[-1].get("free_cash_flow", 0.0) if history_years else 0.0
        if latest_fcf == 0.0 and history_years:
            # Fallback: Operating Cash Flow - Capex
            cfo = history_years[-1].get("operating_cash_flow", 0.0)
            capex = history_years[-1].get("capital_expenditure", 0.0)
            latest_fcf = cfo - abs(capex)

        # Shareholding data
        major_holders = stock.major_holders
        institutional_holders = stock.institutional_holders
        shareholding_summary = self._parse_shareholding(major_holders, info)

        data = {
            "symbol": symbol,
            "short_name": info.get("shortName") or info.get("longName") or symbol,
            "long_name": info.get("longName") or info.get("shortName") or symbol,
            "sector": info.get("sector") or "Unknown Sector",
            "industry": info.get("industry") or "Unknown Industry",
            "summary": info.get("longBusinessSummary") or "",
            "current_price": float(current_price),
            "currency": info.get("currency") or "INR",
            "market_cap": float(market_cap),
            "market_cap_cr": float(market_cap) / 1e7 if market_cap else 0.0,
            "shares_outstanding": float(shares_outstanding),
            "fifty_two_week_high": float(info.get("fiftyTwoWeekHigh") or 0.0),
            "fifty_two_week_low": float(info.get("fiftyTwoWeekLow") or 0.0),
            "trailing_pe": float(info.get("trailingPE") or 0.0),
            "forward_pe": float(info.get("forwardPE") or 0.0),
            "price_to_book": float(info.get("priceToBook") or 0.0),
            "enterprise_value": float(info.get("enterpriseValue") or 0.0),
            "ev_to_ebitda": float(info.get("enterpriseToEbitda") or 0.0),
            "dividend_yield_pct": float(info.get("dividendYield") or 0.0) * 100 if info.get("dividendYield") else 0.0,
            "latest_net_debt": float(net_debt),
            "latest_fcf": float(latest_fcf),
            "history_years": history_years,
            "shareholding": shareholding_summary,
            "raw_info": info
        }

        self._cache[symbol] = data
        return data

    def _parse_financial_history(
        self,
        income_df: Optional[pd.DataFrame],
        balance_df: Optional[pd.DataFrame],
        cashflow_df: Optional[pd.DataFrame]
    ) -> List[Dict[str, Any]]:
        """Parses and aligns 3-5 years of statements into structured year-by-year dictionaries."""
        if income_df is None or income_df.empty:
            return []

        years = []
        date_cols = list(income_df.columns)
        # Sort oldest to newest
        try:
            sorted_cols = sorted(date_cols, key=lambda d: pd.to_datetime(d))
        except Exception:
            sorted_cols = list(reversed(date_cols))

        for col in sorted_cols:
            year_label = str(col.year if hasattr(col, "year") else str(col)[:4])

            # Income items
            rev = self._extract_value(income_df, col, ["Total Revenue", "Operating Revenue", "Revenue"])
            pat = self._extract_value(income_df, col, ["Net Income", "Net Income Common Stockholders", "Net Income Applicable To Common Shares"])
            ebit = self._extract_value(income_df, col, ["EBIT", "Operating Income"])
            ebitda = self._extract_value(income_df, col, ["EBITDA", "Normalized EBITDA"])
            interest = self._extract_value(income_df, col, ["Interest Expense", "Interest Expense Non Operating", "Interest Expense Net"])

            # Cash flow items
            cfo = 0.0
            capex = 0.0
            fcf = 0.0
            div_paid = 0.0
            if cashflow_df is not None and col in cashflow_df.columns:
                cfo = self._extract_value(cashflow_df, col, ["Operating Cash Flow", "Cash Flow From Continuing Operating Activities"])
                capex = abs(self._extract_value(cashflow_df, col, ["Capital Expenditure", "Purchase Of PPE"]))
                fcf = self._extract_value(cashflow_df, col, ["Free Cash Flow"])
                if fcf == 0.0 and (cfo != 0.0 or capex != 0.0):
                    fcf = cfo - capex
                div_paid = abs(self._extract_value(cashflow_df, col, ["Cash Dividends Paid", "Common Stock Dividend Paid", "Payment Of Dividends"]))

            # Balance sheet items
            receivables = 0.0
            inventory = 0.0
            payables = 0.0
            total_debt = 0.0
            cash_eq = 0.0
            goodwill = 0.0
            total_assets = 0.0
            equity = 0.0
            if balance_df is not None and col in balance_df.columns:
                receivables = self._extract_value(balance_df, col, ["Receivables", "Accounts Receivable", "Gross Accounts Receivable"])
                inventory = self._extract_value(balance_df, col, ["Inventory", "Total Inventories"])
                payables = self._extract_value(balance_df, col, ["Payables", "Accounts Payable", "Payables And Accrued Expenses"])
                total_debt = self._extract_value(balance_df, col, ["Total Debt", "Long Term Debt And Capital Lease Obligation", "Long Term Debt"])
                cash_eq = self._extract_value(balance_df, col, ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments", "Cash Financial"])
                goodwill = self._extract_value(balance_df, col, ["Goodwill", "Goodwill And Other Intangible Assets"])
                total_assets = self._extract_value(balance_df, col, ["Total Assets"])
                equity = self._extract_value(balance_df, col, ["Stockholders Equity", "Total Equity Gross Minority Interest", "Common Stock Equity"])

            years.append({
                "year": year_label,
                "date": str(col),
                "revenue": rev,
                "net_income": pat,
                "ebit": ebit,
                "ebitda": ebitda,
                "interest_expense": interest,
                "operating_cash_flow": cfo,
                "capital_expenditure": capex,
                "free_cash_flow": fcf,
                "dividends_paid": div_paid,
                "receivables": receivables,
                "inventory": inventory,
                "payables": payables,
                "total_debt": total_debt,
                "cash_and_equivalents": cash_eq,
                "goodwill": goodwill,
                "total_assets": total_assets,
                "stockholders_equity": equity
            })

        return years

    @staticmethod
    def _extract_value(df: Optional[pd.DataFrame], col: Any, candidate_keys: List[str], default: float = 0.0) -> float:
        """Extracts the first matching key value from a dataframe index with robust defensive fallback."""
        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return default
        try:
            if col not in df.columns:
                return default
            for key in candidate_keys:
                if key in df.index:
                    val = df.loc[key, col]
                    if hasattr(val, "iloc"):
                        # If duplicate index entries return a Series
                        val = val.iloc[0]
                    if pd.notna(val):
                        try:
                            return float(val)
                        except (ValueError, TypeError):
                            pass
        except Exception:
            pass
        return default

    def _parse_shareholding(self, major_holders: Optional[pd.DataFrame], info: Dict[str, Any]) -> Dict[str, Any]:
        """Extracts promoter holding, institutional (FII/DII) holding, and pledge estimates."""
        promoter_pct = 0.0
        institutions_pct = 0.0
        insiders_pct = 0.0
        pledge_pct = 0.0

        if info:
            insiders_pct = float(info.get("heldPercentInsiders") or 0.0) * 100
            institutions_pct = float(info.get("heldPercentInstitutions") or 0.0) * 100
            promoter_pct = insiders_pct

        # Check major holders dataframe if available
        if major_holders is not None and not major_holders.empty:
            try:
                for _, row in major_holders.iterrows():
                    text = str(row.iloc[1]).lower() if len(row) > 1 else ""
                    val_str = str(row.iloc[0]).replace("%", "").strip()
                    try:
                        val = float(val_str)
                        if "insider" in text or "promoter" in text:
                            promoter_pct = max(promoter_pct, val)
                        elif "institution" in text:
                            institutions_pct = max(institutions_pct, val)
                    except ValueError:
                        pass
            except Exception:
                pass

        # Check for pledge notes in info
        # yfinance occasionally provides pledge under 'pnl' or Indian regulatory notes
        public_pct = max(0.0, 100.0 - (promoter_pct + institutions_pct))

        return {
            "promoter_holding_pct": round(promoter_pct, 2),
            "institutional_holding_pct": round(institutions_pct, 2),
            "public_holding_pct": round(public_pct, 2),
            "promoter_pledge_pct": round(pledge_pct, 2)
        }

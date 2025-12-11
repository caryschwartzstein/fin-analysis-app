import yfinance as yf
import pandas as pd
import time
from typing import Optional, Dict, Any


class YFinanceService:
    """Service class to interact with Yahoo Finance via yfinance library."""

    def __init__(self):
        self._cache = {}  # Simple cache to avoid repeated requests
        self._last_request_time = 0
        self._min_request_interval = 0.5  # Minimum 0.5 seconds between requests

    def _rate_limit(self):
        """Implement simple rate limiting to avoid Yahoo Finance blocking."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last_request)

        self._last_request_time = time.time()

    def get_financials(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1
    ) -> Optional[list]:
        """
        Get financial statements for a ticker using yfinance.

        Args:
            ticker: Stock ticker symbol
            timeframe: 'annual' or 'quarterly'
            limit: Number of periods to retrieve (max 4 for yfinance)

        Returns:
            List of financial data or None if not found
        """
        print(f"Fetching financials for {ticker} from yfinance.")
        try:
            # Check cache first
            cache_key = f"{ticker}_{timeframe}_{limit}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            # self._rate_limit()
            print(f"GOT HERE 1 {ticker} {timeframe} {limit}")
            stock = yf.Ticker(ticker.upper())
            print(f"GOT HERE 2 {ticker} {stock.info}")


            # Get financial statements based on timeframe
            if timeframe == "annual":
                income_stmt = stock.financials
                balance_sheet = stock.balance_sheet
            else:  # quarterly
                income_stmt = stock.quarterly_financials
                balance_sheet = stock.quarterly_balance_sheet

            # Check if data is available
            if income_stmt.empty or balance_sheet.empty:
                return None
            print(f"GOT HERE 3 {ticker} {timeframe} {limit}")
            # yfinance returns DataFrames with columns as dates
            # We need to convert to list format similar to Polygon
            results = []

            # Get up to 'limit' periods
            num_periods = min(limit, len(income_stmt.columns))

            for i in range(num_periods):
                period_data = {
                    "end_date": income_stmt.columns[i].strftime('%Y-%m-%d'),
                    "fiscal_period": "FY" if timeframe == "annual" else f"Q{((i % 4) + 1)}",
                    "fiscal_year": str(income_stmt.columns[i].year),
                    "financials": {
                        "income_statement": income_stmt.iloc[:, i].to_dict(),
                        "balance_sheet": balance_sheet.iloc[:, i].to_dict()
                    }
                }
                results.append(period_data)

            # Cache the results
            if results:
                self._cache[cache_key] = results

            print(f"RESULTS HERE {results}")

            return results if results else None

        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            return None

    def extract_income_statement(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract income statement fields from yfinance financial data.

        Args:
            financial_data: Raw financial data from yfinance

        Returns:
            Extracted income statement fields
        """
        income_statement = financial_data.get("financials", {}).get("income_statement", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Revenue fields
            "revenues": self._safe_get(income_statement, 'Total Revenue'),
            # Operating income (EBIT - Earnings Before Interest and Taxes)
            "operating_income_loss": self._safe_get(income_statement, 'Operating Income'),
            # EBITDA
            "ebitda": self._safe_get(income_statement, 'EBITDA'),
            # Net income
            "net_income_loss": self._safe_get(income_statement, 'Net Income'),
            # Cost of revenue
            "cost_of_revenue": self._safe_get(income_statement, 'Cost Of Revenue'),
            # Gross profit
            "gross_profit": self._safe_get(income_statement, 'Gross Profit'),
            # Operating expenses
            "operating_expenses": self._safe_get(income_statement, 'Operating Expense'),
            # Interest expense (for reference)
            "interest_expense": self._safe_get(income_statement, 'Interest Expense'),
        }

    def extract_balance_sheet(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract balance sheet fields from yfinance financial data.

        Args:
            financial_data: Raw financial data from yfinance

        Returns:
            Extracted balance sheet fields
        """
        balance_sheet = financial_data.get("financials", {}).get("balance_sheet", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Current assets
            "current_assets": self._safe_get(balance_sheet, 'Current Assets'),
            # Current liabilities
            "current_liabilities": self._safe_get(balance_sheet, 'Current Liabilities'),
            # Fixed assets (Property, Plant & Equipment)
            "fixed_assets": self._safe_get(balance_sheet, 'Net PPE'),
            # Total assets
            "assets": self._safe_get(balance_sheet, 'Total Assets'),
            # Total liabilities
            "liabilities": self._safe_get(balance_sheet, 'Total Liabilities Net Minority Interest'),
            # Equity
            "equity": self._safe_get(balance_sheet, 'Stockholders Equity'),
            # Cash and equivalents (try multiple field names)
            "cash_and_equivalents": (
                self._safe_get(balance_sheet, 'Cash And Cash Equivalents') or
                self._safe_get(balance_sheet, 'Cash Cash Equivalents And Short Term Investments')
            ),
            # Debt components for Enterprise Value calculation
            # Note: Not all companies report these separately
            # Keep existing fallbacks (they make sense for yfinance field naming)
            "current_debt": (
                self._safe_get(balance_sheet, 'Current Debt') or
                self._safe_get(balance_sheet, 'Current Debt And Capital Lease Obligation')
            ),
            "long_term_debt": (
                self._safe_get(balance_sheet, 'Long Term Debt') or
                self._safe_get(balance_sheet, 'Long Term Debt And Capital Lease Obligation')
            ),
            # Total debt (if available)
            "short_long_term_debt_total": self._safe_get(balance_sheet, 'Total Debt'),
            # Individual debt fields for transparency
            "short_term_debt": self._safe_get(balance_sheet, 'Short Term Debt'),
            "current_long_term_debt": self._safe_get(balance_sheet, 'Current Long Term Debt'),
            "long_term_debt_noncurrent": self._safe_get(balance_sheet, 'Long Term Debt Noncurrent'),
        }

    def get_ticker_details(self, ticker: str) -> Optional[Dict[str, Any]]:
        """
        Get ticker details including market cap and shares outstanding.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Dictionary with ticker details or None if not found
        """
        try:
            # Check cache first
            cache_key = f"details_{ticker}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            self._rate_limit()
            stock = yf.Ticker(ticker.upper())

            # Use fast_info if available (less data, faster, fewer rate limit issues)
            try:
                fast_info = stock.fast_info
                market_cap = fast_info.get('market_cap') if hasattr(fast_info, 'get') else getattr(fast_info, 'market_cap', None)
                shares = fast_info.get('shares') if hasattr(fast_info, 'get') else getattr(fast_info, 'shares', None)

                result = {
                    "ticker": ticker.upper(),
                    "market_cap": market_cap,
                    "share_class_shares_outstanding": shares,
                    "weighted_shares_outstanding": shares,
                }

                # Cache the result
                self._cache[cache_key] = result
                return result
            except:
                # Fallback to regular info (slower, more prone to rate limits)
                info = stock.info

                # Calculate market cap if not available
                market_cap = info.get('marketCap')
                shares_outstanding = info.get('sharesOutstanding')
                current_price = info.get('currentPrice')

                # Fallback: calculate market cap from price and shares
                if not market_cap and current_price and shares_outstanding:
                    market_cap = current_price * shares_outstanding

                result = {
                    "ticker": ticker.upper(),
                    "market_cap": market_cap,
                    "share_class_shares_outstanding": shares_outstanding,
                    "weighted_shares_outstanding": shares_outstanding,
                }

                # Cache the result
                self._cache[cache_key] = result
                return result

        except Exception as e:
            print(f"Error fetching ticker details for {ticker}: {e}")
            return None

    @staticmethod
    def _safe_get(data_dict: Dict, key: str) -> Optional[float]:
        """
        Safely get value from dictionary, handling NaN and missing values.

        Args:
            data_dict: Dictionary to extract from
            key: Key to look for

        Returns:
            Float value or None if not available
        """
        try:
            value = data_dict.get(key)
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            return float(value)
        except (TypeError, ValueError, KeyError):
            return None


# Create a single instance to be used throughout the app
yfinance_service = YFinanceService()

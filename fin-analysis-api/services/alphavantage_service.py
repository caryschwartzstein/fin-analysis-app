"""Alpha Vantage service for fetching financial data from SEC filings."""
import time
from typing import Optional, Dict, Any
from alpha_vantage.fundamentaldata import FundamentalData
from config import settings


class AlphaVantageService:
    """Service class to interact with Alpha Vantage API for fundamental data."""

    def __init__(self):
        self._cache = {}  # Simple cache to avoid repeated requests
        self._last_request_time = 0
        self._min_request_interval = 12  # 5 requests/minute = 12 seconds between requests
        self._daily_request_count = 0
        self._daily_limit = 25  # Free tier limit
        self._last_reset_date = None

    def _check_daily_limit(self):
        """Check if daily request limit has been reached."""
        import datetime
        today = datetime.date.today()

        # Reset counter if it's a new day
        if self._last_reset_date != today:
            self._daily_request_count = 0
            self._last_reset_date = today

        # Check if we've hit the limit
        if self._daily_request_count >= self._daily_limit:
            raise Exception(f"Alpha Vantage daily limit of {self._daily_limit} requests reached. Try again tomorrow.")

    def _rate_limit(self):
        """Implement rate limiting to comply with Alpha Vantage limits."""
        current_time = time.time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            time.sleep(self._min_request_interval - time_since_last_request)

        self._last_request_time = time.time()

    def _increment_request_count(self):
        """Increment the daily request counter."""
        self._daily_request_count += 1

    def get_financials(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1
    ) -> Optional[list]:
        """
        Get financial statements for a ticker using Alpha Vantage.

        Args:
            ticker: Stock ticker symbol
            timeframe: 'annual' or 'quarterly'
            limit: Number of periods to retrieve

        Returns:
            List of financial data or None if not found
        """
        try:
            # Check cache first
            cache_key = f"{ticker}_{timeframe}_{limit}"
            if cache_key in self._cache:
                return self._cache[cache_key]

            # Check daily limit
            self._check_daily_limit()

            # Rate limit
            self._rate_limit()

            # Initialize Alpha Vantage client
            fd = FundamentalData(key=settings.alpha_vantage_api_key, output_format='pandas')

            # Get income statement and balance sheet
            if timeframe == "annual":
                income_df, _ = fd.get_income_statement_annual(symbol=ticker.upper())
                balance_df, _ = fd.get_balance_sheet_annual(symbol=ticker.upper())
            else:  # quarterly
                income_df, _ = fd.get_income_statement_quarterly(symbol=ticker.upper())
                balance_df, _ = fd.get_balance_sheet_quarterly(symbol=ticker.upper())

            # Increment request count (2 requests made: income + balance)
            self._increment_request_count()
            self._increment_request_count()

            # Check if data is available
            if income_df.empty or balance_df.empty:
                return None

            # Alpha Vantage returns DataFrames with rows as periods and columns as fields
            # Convert to our format (list of periods)
            results = []

            # Get up to 'limit' periods (rows are periods)
            num_periods = min(limit, len(income_df))

            for i in range(num_periods):
                # Get the date for this period from the fiscalDateEnding column
                fiscal_date = income_df.iloc[i]['fiscalDateEnding']

                # Convert DataFrame row to dictionary
                income_dict = income_df.iloc[i].to_dict()
                balance_dict = balance_df.iloc[i].to_dict()

                period_data = {
                    "end_date": fiscal_date,
                    "fiscal_period": "FY" if timeframe == "annual" else f"Q{((i % 4) + 1)}",
                    "fiscal_year": fiscal_date.split('-')[0] if fiscal_date else None,  # Extract year from date
                    "financials": {
                        "income_statement": income_dict,
                        "balance_sheet": balance_dict
                    }
                }
                results.append(period_data)

            # Cache the results
            if results:
                self._cache[cache_key] = results

            return results if results else None

        except Exception as e:
            print(f"Error fetching financials from Alpha Vantage for {ticker}: {e}")
            return None

    def extract_income_statement(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract income statement fields from Alpha Vantage financial data.

        Args:
            financial_data: Raw financial data from Alpha Vantage

        Returns:
            Extracted income statement fields
        """
        income_statement = financial_data.get("financials", {}).get("income_statement", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Revenue fields
            "revenues": self._safe_get(income_statement, 'totalRevenue'),
            # Operating income (EBIT)
            "operating_income_loss": self._safe_get(income_statement, 'operatingIncome'),
            # EBITDA
            "ebitda": self._safe_get(income_statement, 'ebitda'),
            # EBIT (Alpha Vantage has this directly!)
            "ebit": self._safe_get(income_statement, 'ebit'),
            # Net income
            "net_income_loss": self._safe_get(income_statement, 'netIncome'),
            # Cost of revenue
            "cost_of_revenue": self._safe_get(income_statement, 'costOfRevenue'),
            # Gross profit
            "gross_profit": self._safe_get(income_statement, 'grossProfit'),
            # Operating expenses
            "operating_expenses": self._safe_get(income_statement, 'operatingExpenses'),
            # Interest expense
            "interest_expense": self._safe_get(income_statement, 'interestExpense'),
        }

    def extract_balance_sheet(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract balance sheet fields from Alpha Vantage financial data.

        Args:
            financial_data: Raw financial data from Alpha Vantage

        Returns:
            Extracted balance sheet fields
        """
        balance_sheet = financial_data.get("financials", {}).get("balance_sheet", {})

        print(f'HEREEE: {balance_sheet}')

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Current assets
            "current_assets": self._safe_get(balance_sheet, 'totalCurrentAssets'),
            # Current liabilities
            "current_liabilities": self._safe_get(balance_sheet, 'totalCurrentLiabilities'),
            # Fixed assets (Property, Plant & Equipment)
            "fixed_assets": self._safe_get(balance_sheet, 'propertyPlantEquipment'),
            # Total assets
            "assets": self._safe_get(balance_sheet, 'totalAssets'),
            # Total liabilities
            "liabilities": self._safe_get(balance_sheet, 'totalLiabilities'),
            # Equity (Shareholder equity)
            "equity": self._safe_get(balance_sheet, 'totalShareholderEquity'),
            # Cash and equivalents
            "cash_and_equivalents": self._safe_get(balance_sheet, 'cashAndCashEquivalentsAtCarryingValue'),
            # Debt components - return all individual fields for transparency
            "short_long_term_debt_total": self._safe_get(balance_sheet, 'shortLongTermDebtTotal'),
            "current_debt": self._safe_get(balance_sheet, 'currentDebt'),
            "short_term_debt": self._safe_get(balance_sheet, 'shortTermDebt'),
            "current_long_term_debt": self._safe_get(balance_sheet, 'currentLongTermDebt'),
            "long_term_debt": self._safe_get(balance_sheet, 'longTermDebt'),
            "long_term_debt_noncurrent": self._safe_get(balance_sheet, 'longTermDebtNoncurrent'),
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

            # Check daily limit
            self._check_daily_limit()

            # Rate limit
            self._rate_limit()

            # Initialize Alpha Vantage client
            fd = FundamentalData(key=settings.alpha_vantage_api_key, output_format='pandas')

            # Get company overview
            overview_df, _ = fd.get_company_overview(symbol=ticker.upper())

            # Increment request count
            self._increment_request_count()

            # Check if data is available
            if overview_df.empty:
                return None

            # Convert to dictionary (overview returns a single-row DataFrame)
            overview = overview_df.to_dict('records')[0] if len(overview_df) > 0 else {}

            # Extract market cap and shares
            market_cap = self._safe_get(overview, 'MarketCapitalization')
            shares_outstanding = self._safe_get(overview, 'SharesOutstanding')

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
            print(f"Error fetching ticker details from Alpha Vantage for {ticker}: {e}")
            return None

    @staticmethod
    def _safe_get(data_dict: Dict, key: str) -> Optional[float]:
        """
        Safely get value from dictionary, handling None and missing values.

        Args:
            data_dict: Dictionary to extract from
            key: Key to look for

        Returns:
            Float value or None if not available
        """
        try:
            value = data_dict.get(key)
            if value is None or value == 'None':
                return None
            return float(value)
        except (TypeError, ValueError, KeyError):
            return None


# Create a single instance to be used throughout the app
alphavantage_service = AlphaVantageService()

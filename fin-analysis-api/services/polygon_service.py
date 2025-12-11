import requests
from typing import Optional, Dict, Any
from config import settings
from services.exceptions import RateLimitError, DataNotFoundError, APIKeyError, FinancialDataError


class PolygonService:
    """Service class to interact with Polygon.io API."""

    def __init__(self):
        self.api_key = settings.polygon_api_key
        self.base_url = "https://api.polygon.io"

    def get_financials(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1
    ) -> Optional[list]:
        """
        Get financial statements for a ticker using Polygon's vX/reference/financials endpoint.

        Args:
            ticker: Stock ticker symbol
            timeframe: 'annual' or 'quarterly'
            limit: Number of periods to retrieve

        Returns:
            List of financial data or None if not found
        """
        try:
            # Polygon uses 'quarterly' not 'quarter'
            if timeframe == "quarter":
                timeframe = "quarterly"

            url = f"{self.base_url}/vX/reference/financials"
            params = {
                "ticker": ticker.upper(),
                "timeframe": timeframe,
                "limit": limit,
                "apiKey": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            if not results:
                raise DataNotFoundError(
                    f"No financial data available for ticker {ticker}. The ticker may be invalid or data is not available from Polygon.",
                    provider="polygon"
                )

            return results

        except requests.exceptions.HTTPError as e:
            # Handle HTTP errors
            if e.response.status_code == 401:
                raise APIKeyError(
                    "Invalid Polygon API key. Please check your API key configuration.",
                    provider="polygon",
                    original_error=e
                )
            elif e.response.status_code == 429:
                raise RateLimitError(
                    "Polygon API rate limit exceeded. Please upgrade your plan or wait before retrying.",
                    provider="polygon",
                    original_error=e
                )
            elif e.response.status_code == 404:
                raise DataNotFoundError(
                    f"Ticker {ticker} not found in Polygon database.",
                    provider="polygon",
                    original_error=e
                )
            else:
                raise FinancialDataError(
                    f"Polygon API error (HTTP {e.response.status_code}): {str(e)}",
                    provider="polygon",
                    original_error=e
                )
        except requests.exceptions.Timeout:
            raise FinancialDataError(
                "Request to Polygon API timed out. Please try again.",
                provider="polygon",
                original_error=e
            )
        except requests.exceptions.ConnectionError as e:
            raise FinancialDataError(
                f"Connection error to Polygon API: {str(e)}",
                provider="polygon",
                original_error=e
            )
        except DataNotFoundError:
            # Re-raise our custom exception
            raise
        except Exception as e:
            print(f"Error fetching financials for {ticker}: {e}")
            raise FinancialDataError(
                f"Polygon error for {ticker}: {str(e)}",
                provider="polygon",
                original_error=e
            )

    def extract_income_statement(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract income statement fields from Polygon financial data.

        Args:
            financial_data: Raw financial data from Polygon API

        Returns:
            Extracted income statement fields
        """
        financials = financial_data.get("financials", {})
        income_statement = financials.get("income_statement", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Revenue fields
            "revenues": income_statement.get("revenues", {}).get("value"),
            # Operating income (EBIT - Earnings Before Interest and Taxes)
            "operating_income_loss": income_statement.get("operating_income_loss", {}).get("value"),
            # EBITDA
            "ebitda": income_statement.get("ebitda", {}).get("value"),
            # Net income
            "net_income_loss": income_statement.get("net_income_loss", {}).get("value"),
            # Cost of revenue
            "cost_of_revenue": income_statement.get("cost_of_revenue", {}).get("value"),
            # Gross profit
            "gross_profit": income_statement.get("gross_profit", {}).get("value"),
            # Operating expenses
            "operating_expenses": income_statement.get("operating_expenses", {}).get("value"),
            # Interest expense (for reference)
            "interest_expense": income_statement.get("interest_expense", {}).get("value"),
        }

    def extract_balance_sheet(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract balance sheet fields from Polygon financial data.

        Args:
            financial_data: Raw financial data from Polygon API

        Returns:
            Extracted balance sheet fields
        """
        financials = financial_data.get("financials", {})
        balance_sheet = financials.get("balance_sheet", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            # Current assets
            "current_assets": balance_sheet.get("current_assets", {}).get("value"),
            # Current liabilities
            "current_liabilities": balance_sheet.get("current_liabilities", {}).get("value"),
            # Fixed assets (Property, Plant & Equipment)
            "fixed_assets": balance_sheet.get("fixed_assets", {}).get("value"),
            # Total assets
            "assets": balance_sheet.get("assets", {}).get("value"),
            # Total liabilities
            "liabilities": balance_sheet.get("liabilities", {}).get("value"),
            # Equity
            "equity": balance_sheet.get("equity", {}).get("value"),
            # Cash and equivalents (try multiple field names from Polygon's schema)
            "cash_and_equivalents": (
                balance_sheet.get("cash_and_equivalents", {}).get("value") or
                balance_sheet.get("cash_and_short_term_investments", {}).get("value") or
                balance_sheet.get("cash", {}).get("value")
            ),
            # Debt components - extract all individual fields for transparency
            # No fallbacks - just return what Polygon provides
            "short_long_term_debt_total": (
                balance_sheet.get("short_long_term_debt_total", {}).get("value") or
                balance_sheet.get("total_debt", {}).get("value")
            ),
            "current_debt": balance_sheet.get("debt_current", {}).get("value"),
            "short_term_debt": balance_sheet.get("short_term_debt", {}).get("value"),
            "current_long_term_debt": balance_sheet.get("current_long_term_debt", {}).get("value"),
            "long_term_debt": balance_sheet.get("long_term_debt", {}).get("value"),
            "long_term_debt_noncurrent": balance_sheet.get("long_term_debt_noncurrent", {}).get("value"),
        }

    def extract_comprehensive_income(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract comprehensive income fields from Polygon financial data.

        Args:
            financial_data: Raw financial data from Polygon API

        Returns:
            Extracted comprehensive income fields
        """
        financials = financial_data.get("financials", {})
        comprehensive_income = financials.get("comprehensive_income", {})

        return {
            "date": financial_data.get("end_date"),
            "fiscal_period": financial_data.get("fiscal_period"),
            "fiscal_year": financial_data.get("fiscal_year"),
            "comprehensive_income_loss": comprehensive_income.get("comprehensive_income_loss", {}).get("value"),
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
            url = f"{self.base_url}/v3/reference/tickers/{ticker.upper()}"
            params = {"apiKey": self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", {})

            if not results:
                raise DataNotFoundError(
                    f"No ticker details found for {ticker} in Polygon database.",
                    provider="polygon"
                )

            return {
                "ticker": ticker.upper(),
                "market_cap": results.get("market_cap"),
                "share_class_shares_outstanding": results.get("share_class_shares_outstanding"),
                "weighted_shares_outstanding": results.get("weighted_shares_outstanding"),
            }

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise APIKeyError(
                    "Invalid Polygon API key. Please check your API key configuration.",
                    provider="polygon",
                    original_error=e
                )
            elif e.response.status_code == 429:
                raise RateLimitError(
                    "Polygon API rate limit exceeded. Please upgrade your plan or wait before retrying.",
                    provider="polygon",
                    original_error=e
                )
            elif e.response.status_code == 404:
                raise DataNotFoundError(
                    f"Ticker {ticker} not found in Polygon database.",
                    provider="polygon",
                    original_error=e
                )
            else:
                raise FinancialDataError(
                    f"Polygon API error (HTTP {e.response.status_code}): {str(e)}",
                    provider="polygon",
                    original_error=e
                )
        except requests.exceptions.Timeout as e:
            raise FinancialDataError(
                "Request to Polygon API timed out. Please try again.",
                provider="polygon",
                original_error=e
            )
        except requests.exceptions.ConnectionError as e:
            raise FinancialDataError(
                f"Connection error to Polygon API: {str(e)}",
                provider="polygon",
                original_error=e
            )
        except DataNotFoundError:
            raise
        except Exception as e:
            print(f"Error fetching ticker details for {ticker}: {e}")
            raise FinancialDataError(
                f"Unable to get ticker details for {ticker} from Polygon: {str(e)}",
                provider="polygon",
                original_error=e
            )

    def get_ratios(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1
    ) -> Optional[list]:
        """
        Get financial ratios including pre-calculated enterprise value.

        Args:
            ticker: Stock ticker symbol
            timeframe: 'annual' or 'quarterly'
            limit: Number of periods to retrieve

        Returns:
            List of ratio data or None if not found
        """
        try:
            url = f"{self.base_url}/vX/reference/ratios"
            params = {
                "ticker": ticker.upper(),
                "timeframe": timeframe,
                "limit": limit,
                "apiKey": self.api_key
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            results = data.get("results", [])

            return results if results else None

        except Exception as e:
            print(f"Error fetching ratios for {ticker}: {e}")
            return None

    def extract_ratios(self, ratio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract key ratios from Polygon ratio data.

        Args:
            ratio_data: Raw ratio data from Polygon API

        Returns:
            Extracted ratio fields
        """
        return {
            "date": ratio_data.get("period_end"),
            "fiscal_period": ratio_data.get("fiscal_period"),
            "fiscal_year": ratio_data.get("fiscal_year"),
            # Valuation metrics
            "enterprise_value": ratio_data.get("enterprise_value"),
            "market_cap": ratio_data.get("market_cap"),
            "stock_price": ratio_data.get("stock_price"),
            # Ratios
            "ev_to_sales": ratio_data.get("ev_to_sales"),
            "ev_to_ebitda": ratio_data.get("ev_to_ebitda"),
            "price_to_earnings": ratio_data.get("price_to_earnings"),
            "price_to_book": ratio_data.get("price_to_book"),
        }


# Create a single instance to be used throughout the app
polygon_service = PolygonService()

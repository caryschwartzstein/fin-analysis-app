"""Hybrid financial data service that supports Polygon, yfinance, and Alpha Vantage."""
from typing import Optional, Dict, Any, Literal
from services.polygon_service import polygon_service
from services.yfinance_service import yfinance_service
from services.alphavantage_service import alphavantage_service
from config import settings


ProviderType = Literal["polygon", "yfinance", "alphavantage"]


class FinancialDataService:
    """
    Unified service that can use Polygon, yfinance, or Alpha Vantage as data providers.
    Supports automatic fallback and provider selection.
    Priority: yfinance > alphavantage > polygon (for personal use)
    """

    def __init__(self):
        self.polygon = polygon_service
        self.yfinance = yfinance_service
        self.alphavantage = alphavantage_service

    def _get_default_provider(self) -> ProviderType:
        """
        Determine the default provider based on configuration.

        Priority for personal use:
        1. yfinance (free, unlimited for reasonable use)
        2. alphavantage (25/day, official API)
        3. polygon (has deprecated endpoint)

        Returns:
            Provider name based on priority and API key availability
        """
        if settings.default_provider:
            return settings.default_provider.lower()

        # Auto-detect with priority: yfinance > alphavantage > polygon
        # yfinance is always available (no API key needed)
        # Use it as default for personal, infrequent use
        return "yfinance"

    def _get_service(self, provider: Optional[str] = None):
        """
        Get the appropriate service instance.

        Args:
            provider: Optional provider name ('polygon', 'yfinance', or 'alphavantage')

        Returns:
            Service instance (polygon_service, yfinance_service, or alphavantage_service)
        """
        if provider is None:
            provider = self._get_default_provider()

        provider_lower = provider.lower()

        if provider_lower == "polygon":
            if not settings.has_polygon_key:
                print("Warning: Polygon provider requested but no API key configured. Falling back to yfinance.")
                return self.yfinance
            return self.polygon
        elif provider_lower == "alphavantage":
            if not settings.has_alpha_vantage_key:
                print("Warning: Alpha Vantage provider requested but no API key configured. Falling back to yfinance.")
                return self.yfinance
            return self.alphavantage
        elif provider_lower == "yfinance":
            return self.yfinance
        else:
            print(f"Warning: Unknown provider '{provider}'. Using default.")
            return self._get_service(None)

    def get_financials(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1,
        provider: Optional[str] = None
    ) -> Optional[tuple[list, str]]:
        """
        Get financial statements using specified provider with automatic fallback.

        Args:
            ticker: Stock ticker symbol
            timeframe: 'annual' or 'quarterly'
            limit: Number of periods to retrieve
            provider: Optional provider override ('polygon' or 'yfinance')

        Returns:
            Tuple of (financial data list, provider used) or (None, None) if failed
        """
        # Determine which provider to use
        selected_provider = provider if provider else self._get_default_provider()
        service = self._get_service(selected_provider)

        try:
            data = service.get_financials(ticker, timeframe, limit)

            if data:
                return data, selected_provider

            # If primary provider returned None and fallback is enabled
            if settings.enable_fallback and selected_provider != "yfinance":
                print(f"{selected_provider} returned no data. Falling back to yfinance.")
                fallback_data = self.yfinance.get_financials(ticker, timeframe, limit)
                if fallback_data:
                    return fallback_data, "yfinance"

            return None, None

        except Exception as e:
            print(f"Error with {selected_provider}: {e}")

            # Fallback to yfinance if enabled and not already using it
            if settings.enable_fallback and selected_provider != "yfinance":
                print(f"Falling back to yfinance due to {selected_provider} error.")
                try:
                    fallback_data = self.yfinance.get_financials(ticker, timeframe, limit)
                    if fallback_data:
                        return fallback_data, "yfinance"
                except Exception as fallback_error:
                    print(f"Fallback to yfinance also failed: {fallback_error}")

            return None, None

    def extract_income_statement(
        self,
        financial_data: Dict[str, Any],
        provider: str
    ) -> Dict[str, Any]:
        """
        Extract income statement using the appropriate provider's method.

        Args:
            financial_data: Raw financial data
            provider: Provider that was used ('polygon' or 'yfinance')

        Returns:
            Extracted income statement data
        """
        service = self._get_service(provider)
        return service.extract_income_statement(financial_data)

    def extract_balance_sheet(
        self,
        financial_data: Dict[str, Any],
        provider: str
    ) -> Dict[str, Any]:
        """
        Extract balance sheet using the appropriate provider's method.

        Args:
            financial_data: Raw financial data
            provider: Provider that was used ('polygon' or 'yfinance')

        Returns:
            Extracted balance sheet data
        """
        service = self._get_service(provider)
        return service.extract_balance_sheet(financial_data)

    def get_ticker_details(
        self,
        ticker: str,
        provider: Optional[str] = None
    ) -> Optional[tuple[Dict[str, Any], str]]:
        """
        Get ticker details (market cap, shares) with automatic fallback.

        Args:
            ticker: Stock ticker symbol
            provider: Optional provider override ('polygon' or 'yfinance')

        Returns:
            Tuple of (ticker details dict, provider used) or (None, None) if failed
        """
        selected_provider = provider if provider else self._get_default_provider()
        service = self._get_service(selected_provider)

        try:
            data = service.get_ticker_details(ticker)

            if data:
                return data, selected_provider

            # Fallback to yfinance if enabled
            if settings.enable_fallback and selected_provider != "yfinance":
                print(f"{selected_provider} ticker details failed. Falling back to yfinance.")
                fallback_data = self.yfinance.get_ticker_details(ticker)
                if fallback_data:
                    return fallback_data, "yfinance"

            return None, None

        except Exception as e:
            print(f"Error getting ticker details with {selected_provider}: {e}")

            # Fallback to yfinance if enabled
            if settings.enable_fallback and selected_provider != "yfinance":
                try:
                    fallback_data = self.yfinance.get_ticker_details(ticker)
                    if fallback_data:
                        return fallback_data, "yfinance"
                except Exception as fallback_error:
                    print(f"Fallback ticker details also failed: {fallback_error}")

            return None, None


# Create a single instance to be used throughout the app
financial_data_service = FinancialDataService()

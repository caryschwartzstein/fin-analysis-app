from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Polygon API key (optional)
    polygon_api_key: Optional[str] = None

    # Alpha Vantage API key (optional)
    alpha_vantage_api_key: Optional[str] = None

    # Default provider: 'polygon', 'yfinance', or 'alphavantage'
    # If not set, will auto-detect with priority: yfinance > alphavantage > polygon
    default_provider: Optional[str] = None

    # Enable fallback to yfinance if other providers fail
    enable_fallback: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"  # Ignore extra fields in .env file
    )

    @property
    def has_polygon_key(self) -> bool:
        """Check if Polygon API key is configured."""
        return self.polygon_api_key is not None and len(self.polygon_api_key.strip()) > 0

    @property
    def has_alpha_vantage_key(self) -> bool:
        """Check if Alpha Vantage API key is configured."""
        return self.alpha_vantage_api_key is not None and len(self.alpha_vantage_api_key.strip()) > 0


# Create a single instance to be imported throughout the app
settings = Settings()
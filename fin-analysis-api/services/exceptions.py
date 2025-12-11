"""Custom exceptions for financial data services"""


class FinancialDataError(Exception):
    """Base exception for financial data errors"""
    def __init__(self, message: str, provider: str = None, original_error: Exception = None):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)


class RateLimitError(FinancialDataError):
    """Exception raised when API rate limit is exceeded"""
    pass


class DataNotFoundError(FinancialDataError):
    """Exception raised when no data is found for a ticker"""
    pass


class APIKeyError(FinancialDataError):
    """Exception raised when API key is invalid or missing"""
    pass

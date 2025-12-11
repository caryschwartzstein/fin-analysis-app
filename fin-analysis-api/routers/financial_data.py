from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Literal
from pydantic import BaseModel
from services.financial_data_service import financial_data_service


router = APIRouter(prefix="/api/v1", tags=["Financial Data"])


class FinancialData(BaseModel):
    """Response model for financial data."""
    ticker: str
    date: str
    fiscal_year: Optional[str] = None
    fiscal_period: Optional[str] = None

    # Income Statement
    revenues: Optional[float] = None
    operating_income: Optional[float] = None
    net_income: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_expenses: Optional[float] = None

    # Balance Sheet
    current_assets: Optional[float] = None
    current_liabilities: Optional[float] = None
    fixed_assets: Optional[float] = None
    total_assets: Optional[float] = None
    total_liabilities: Optional[float] = None
    equity: Optional[float] = None

    # Calculated Metrics
    working_capital: Optional[float] = None
    roce: Optional[float] = None
    roce_percent: Optional[str] = None


class StockMetrics(BaseModel):
    """Response model for calculated stock metrics."""
    ticker: str
    date: str
    period: str

    # ROCE metrics
    roce: Optional[float] = None
    roce_percent: Optional[str] = None
    working_capital: Optional[float] = None
    capital_employed: Optional[float] = None

    # Earnings Yield metrics
    earnings_yield: Optional[float] = None
    earnings_yield_percent: Optional[str] = None
    ebit: Optional[float] = None

    # Enterprise Value components
    enterprise_value: Optional[float] = None
    market_cap: Optional[float] = None

    # EV calculation components
    stock_price: Optional[float] = None
    shares_outstanding: Optional[float] = None
    total_debt: Optional[float] = None
    cash_and_equivalents: Optional[float] = None

    # Balance sheet items
    total_assets: Optional[float] = None
    current_liabilities: Optional[float] = None

    # Debt components (individual fields for transparency)
    short_long_term_debt_total: Optional[float] = None  # Most reliable total debt field
    current_debt: Optional[float] = None  # Total debt due within 1 year (synonymous with short_term_debt)
    short_term_debt: Optional[float] = None  # Short-term debt due within 1 year (synonymous with current_debt)
    current_long_term_debt: Optional[float] = None  # Current portion of long-term debt (CPLTD - component of current_debt)
    long_term_debt: Optional[float] = None  # Long-term debt (may include or exclude current portion depending on provider)
    long_term_debt_noncurrent: Optional[float] = None  # Long-term debt excluding current portion

    notes: list[str] = []


def calculate_roce(operating_income: float, total_assets: float, current_liabilities: float) -> Optional[float]:
    """
    Calculate Return on Capital Employed (ROCE).

    Formula: Operating Income / (Total Assets - Current Liabilities)

    Args:
        operating_income: Operating income (EBIT)
        total_assets: Total assets
        current_liabilities: Current liabilities

    Returns:
        ROCE as a decimal (e.g., 0.15 for 15%), or None if calculation is invalid
    """
    capital_employed = total_assets - current_liabilities

    if capital_employed == 0:
        return None

    return operating_income / capital_employed


def calculate_market_cap(stock_price: float, shares_outstanding: float) -> Optional[float]:
    """
    Calculate Market Capitalization.

    Formula: Stock Price × Shares Outstanding

    Args:
        stock_price: Current stock price
        shares_outstanding: Number of shares outstanding

    Returns:
        Market cap or None if calculation is invalid
    """
    if not stock_price or not shares_outstanding:
        return None
    return stock_price * shares_outstanding


def calculate_total_debt(
    current_debt: Optional[float],
    long_term_debt: Optional[float],
    short_long_term_debt_total: Optional[float] = None
) -> float:
    """
    Calculate Total Debt.

    Formula: Uses short_long_term_debt_total if available, otherwise Current Debt + Long Term Debt

    Args:
        current_debt: Short-term debt and current portion of long-term debt
        long_term_debt: Long-term debt and capital lease obligations
        short_long_term_debt_total: Total debt if reported directly (most reliable)

    Returns:
        Total debt
    """
    # Prefer the directly reported total debt field
    if short_long_term_debt_total is not None:
        return short_long_term_debt_total

    # Fallback to calculating from components
    return (current_debt or 0) + (long_term_debt or 0)


def calculate_enterprise_value(
    market_cap: Optional[float],
    total_debt: float,
    cash_and_equivalents: Optional[float]
) -> Optional[float]:
    """
    Calculate Enterprise Value.

    Formula: Market Cap + Total Debt - Cash & Cash Equivalents

    Args:
        market_cap: Market capitalization
        total_debt: Total debt (current + long-term)
        cash_and_equivalents: Cash and cash equivalents

    Returns:
        Enterprise value or None if market cap is not available
    """
    if not market_cap:
        return None

    cash = cash_and_equivalents or 0
    return market_cap + total_debt - cash


def calculate_earnings_yield(ebit: Optional[float], enterprise_value: Optional[float]) -> Optional[float]:
    """
    Calculate Earnings Yield.

    Formula: EBIT / Enterprise Value

    Args:
        ebit: Earnings Before Interest and Taxes (Operating Income)
        enterprise_value: Enterprise Value

    Returns:
        Earnings yield as a decimal (e.g., 0.08 for 8%), or None if calculation is invalid
    """
    if not ebit or not enterprise_value or enterprise_value == 0:
        return None

    return ebit / enterprise_value


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "Financial Data API", "provider": "Yahoo Finance (yfinance)"}


@router.get("/financials/{ticker}", response_model=FinancialData)
async def get_financial_data(
    ticker: str,
    timeframe: str = Query(default="annual", pattern="^(annual|quarterly)$"),
    limit: int = Query(default=1, ge=1, le=10),
    provider: Optional[str] = Query(None, description="Data provider: 'polygon' or 'yfinance'")
):
    """
    Get comprehensive financial data for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        timeframe: 'annual' or 'quarterly' (default: annual)
        limit: Number of periods to retrieve (1-10, default: 1)
        provider: Optional data provider ('polygon' or 'yfinance'). Defaults to polygon if API key available, otherwise yfinance.

    Returns:
        Financial data including income statement and balance sheet
    """
    ticker = ticker.strip().upper()

    try:
        # Fetch data from financial data service with optional provider
        result = financial_data_service.get_financials(ticker, timeframe=timeframe, limit=limit, provider=provider)

        # Validate response
        if not result or result[0] is None:
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for ticker {ticker}. Verify the ticker symbol."
            )

        financials_data, provider_used = result

        # Validate data
        if not financials_data or len(financials_data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No financial data found for ticker {ticker}. Verify the ticker symbol."
            )

        # Extract latest financial data
        latest = financials_data[0]

        # Extract statements using the appropriate provider's methods
        income = financial_data_service.extract_income_statement(latest, provider_used)
        balance = financial_data_service.extract_balance_sheet(latest, provider_used)

        # Calculate working capital and ROCE
        current_assets = balance.get('current_assets') or 0
        current_liabilities = balance.get('current_liabilities') or 0
        working_capital = current_assets - current_liabilities

        total_assets = balance.get('assets') or 0
        operating_income = income.get('operating_income_loss')

        roce = None
        if operating_income and total_assets and current_liabilities is not None:
            capital_employed = total_assets - current_liabilities
            if capital_employed != 0:
                roce = calculate_roce(operating_income, total_assets, current_liabilities)

        return FinancialData(
            ticker=ticker,
            date=income.get('date'),
            fiscal_year=income.get('fiscal_year'),
            fiscal_period=income.get('fiscal_period'),
            # Income Statement
            revenues=income.get('revenues'),
            operating_income=income.get('operating_income_loss'),
            net_income=income.get('net_income_loss'),
            cost_of_revenue=income.get('cost_of_revenue'),
            gross_profit=income.get('gross_profit'),
            operating_expenses=income.get('operating_expenses'),
            # Balance Sheet
            current_assets=balance.get('current_assets'),
            current_liabilities=balance.get('current_liabilities'),
            fixed_assets=balance.get('fixed_assets'),
            total_assets=balance.get('assets'),
            total_liabilities=balance.get('liabilities'),
            equity=balance.get('equity'),
            # Calculated
            working_capital=working_capital,
            roce=roce,
            roce_percent=f"{roce * 100:.2f}%" if roce else None
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching financial data for {ticker}: {str(e)}"
        )


@router.get("/metrics/{ticker}", response_model=StockMetrics)
async def get_stock_metrics(
    ticker: str,
    timeframe: str = Query(default="annual", pattern="^(annual|quarterly)$"),
    provider: Optional[str] = Query(None, description="Data provider: 'polygon' or 'yfinance'")
):
    """
    Get calculated metrics including ROCE and Earnings Yield for a stock ticker.

    Args:
        ticker: Stock ticker symbol (e.g., AAPL, MSFT)
        timeframe: 'annual' or 'quarterly' (default: annual)
        provider: Optional data provider ('polygon' or 'yfinance'). Defaults to polygon if API key available, otherwise yfinance.

    Returns:
        Calculated stock metrics including ROCE and Earnings Yield
    """
    ticker = ticker.strip().upper()
    notes = []

    try:
        # Fetch data from financial data service with optional provider
        result = financial_data_service.get_financials(ticker, timeframe=timeframe, limit=1, provider=provider)

        # Validate response
        if not result or result[0] is None:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {ticker}. Please verify the ticker symbol."
            )

        financials_data, provider_used = result

        # Validate data
        if not financials_data or len(financials_data) == 0:
            raise HTTPException(
                status_code=404,
                detail=f"No data found for ticker {ticker}. Please verify the ticker symbol."
            )

        # Extract latest financial data
        latest = financials_data[0]

        # Extract statements using the appropriate provider's methods
        income = financial_data_service.extract_income_statement(latest, provider_used)
        balance = financial_data_service.extract_balance_sheet(latest, provider_used)

        # Extract values for ROCE
        operating_income = income.get('operating_income_loss')
        current_assets = balance.get('current_assets') or 0
        current_liabilities = balance.get('current_liabilities') or 0
        total_assets = balance.get('assets') or 0

        working_capital = current_assets - current_liabilities
        capital_employed = total_assets - current_liabilities

        # Calculate ROCE
        roce = None
        if operating_income is None:
            notes.append("Operating income not available")
        elif capital_employed == 0:
            notes.append("Capital employed is zero - cannot calculate ROCE")
        else:
            roce = calculate_roce(operating_income, total_assets, current_liabilities)

        # Extract values for Earnings Yield
        ebit = operating_income  # Operating income is EBIT

        # Extract all individual debt fields for transparency
        current_debt = balance.get('current_debt')
        long_term_debt = balance.get('long_term_debt')
        short_long_term_debt_total = balance.get('short_long_term_debt_total')
        short_term_debt = balance.get('short_term_debt')
        current_long_term_debt = balance.get('current_long_term_debt')
        long_term_debt_noncurrent = balance.get('long_term_debt_noncurrent')
        cash_and_equivalents = balance.get('cash_and_equivalents')

        # Use short_term_debt as fallback for current_debt (they are synonymous)
        if current_debt is None and short_term_debt is not None:
            current_debt = short_term_debt
            notes.append("Current debt using short_term_debt (synonymous terms)")

        # Calculate long_term_debt_noncurrent if not available
        # long_term_debt_noncurrent = total_debt - current_debt OR long_term_debt - current_long_term_debt
        if long_term_debt_noncurrent is None:
            if short_long_term_debt_total is not None and current_debt is not None:
                long_term_debt_noncurrent = short_long_term_debt_total - current_debt
                if long_term_debt_noncurrent > 0:
                    notes.append("Long-term debt noncurrent calculated from total_debt - current_debt")
            elif long_term_debt is not None and current_long_term_debt is not None:
                long_term_debt_noncurrent = long_term_debt - current_long_term_debt
                if long_term_debt_noncurrent > 0:
                    notes.append("Long-term debt noncurrent calculated from long_term_debt - current_long_term_debt")

        # Get ticker details (has market cap and shares outstanding)
        ticker_details_result = financial_data_service.get_ticker_details(ticker, provider=provider)
        market_cap = None
        shares_outstanding = None
        stock_price = None

        if ticker_details_result and ticker_details_result[0]:
            ticker_details, _ = ticker_details_result
            market_cap = ticker_details.get('market_cap')
            shares_outstanding = ticker_details.get('weighted_shares_outstanding')

            # Calculate stock price from market cap and shares
            if market_cap and shares_outstanding and shares_outstanding > 0:
                stock_price = market_cap / shares_outstanding

        # Calculate total debt for Enterprise Value
        # Prefer short_long_term_debt_total if available (most reliable)
        total_debt = calculate_total_debt(current_debt, long_term_debt, short_long_term_debt_total)

        # Calculate enterprise value using our formula
        enterprise_value = calculate_enterprise_value(
            market_cap,
            total_debt,
            cash_and_equivalents
        )

        # Add note if cash data is missing
        if not cash_and_equivalents:
            notes.append("Cash and cash equivalents not reported separately - EV calculation may be overstated")

        # Calculate Earnings Yield
        earnings_yield = calculate_earnings_yield(ebit, enterprise_value)

        if not enterprise_value:
            notes.append("Enterprise value not available - cannot calculate earnings yield")
        elif not ebit:
            notes.append("EBIT not available - cannot calculate earnings yield")

        return StockMetrics(
            ticker=ticker,
            date=income.get('date'),
            period=timeframe,
            # ROCE metrics
            roce=roce,
            roce_percent=f"{roce * 100:.2f}%" if roce else None,
            working_capital=working_capital,
            capital_employed=capital_employed,
            # Earnings Yield metrics
            earnings_yield=earnings_yield,
            earnings_yield_percent=f"{earnings_yield * 100:.2f}%" if earnings_yield else None,
            ebit=ebit,
            # Enterprise Value components
            enterprise_value=enterprise_value,
            market_cap=market_cap,
            # EV calculation components
            stock_price=stock_price,
            shares_outstanding=shares_outstanding,
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            # Balance sheet items
            total_assets=total_assets,
            current_liabilities=current_liabilities,
            # Debt components (individual fields for transparency)
            short_long_term_debt_total=short_long_term_debt_total,
            current_debt=current_debt,
            short_term_debt=short_term_debt,
            current_long_term_debt=current_long_term_debt,
            long_term_debt=long_term_debt,
            long_term_debt_noncurrent=long_term_debt_noncurrent,
            notes=notes
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing metrics for {ticker}: {str(e)}"
        )

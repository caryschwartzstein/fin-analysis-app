# Development Guide

This guide provides detailed information for developers working on the Financial Analysis Dashboard project.

## Table of Contents

- [Project Architecture](#project-architecture)
- [Development Environment Setup](#development-environment-setup)
- [Code Structure](#code-structure)
- [Adding New Features](#adding-new-features)
- [Error Handling Patterns](#error-handling-patterns)
- [Testing](#testing)
- [Deployment](#deployment)
- [Best Practices](#best-practices)

---

## Project Architecture

### High-Level Overview

```
┌─────────────────┐
│  React Frontend │
│  (Port 5173)    │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────┐
│   FastAPI Backend       │
│   (Port 8000)           │
│   ┌─────────────────┐   │
│   │ Routers         │   │
│   └────────┬────────┘   │
│            │             │
│   ┌────────▼────────┐   │
│   │ Services        │   │
│   │ ┌──────────┐    │   │
│   │ │Financial │    │   │
│   │ │Data Svc  │    │   │
│   │ └────┬─────┘    │   │
│   │      │           │   │
│   │  ┌───▼───┬───┬──┐ │
│   │  │yfinance│AV │P│ │
│   │  └────────┴───┴──┘ │
│   └─────────────────┘   │
└─────────────────────────┘
         │ API Calls
         ▼
┌─────────────────────────┐
│  External APIs          │
│  ├─ Yahoo Finance       │
│  ├─ Alpha Vantage       │
│  ├─ Polygon.io          │
│  └─ Schwab              │
└─────────────────────────┘
```

### Request Flow

1. **User Input**: User enters ticker in React frontend
2. **API Call**: Frontend calls `/api/v1/metrics/{ticker}`
3. **Router**: `financial_data.py` receives request
4. **Service Layer**: `financial_data_service.py` orchestrates provider calls
5. **Provider**: Specific provider service (yfinance, alphavantage, polygon)
6. **Data Processing**: Extract and transform data
7. **Calculations**: Calculate ROCE, Earnings Yield, etc.
8. **Response**: Return JSON response to frontend
9. **Display**: Frontend renders metrics

### Error Handling Flow

```
Provider Error
    │
    ▼
Custom Exception Raised
(RateLimitError, DataNotFoundError, etc.)
    │
    ▼
Financial Data Service
(Attempts fallback if applicable)
    │
    ▼
Router Layer
(Maps to HTTP status code)
    │
    ▼
Frontend
(Displays error message)
```

---

## Development Environment Setup

### Backend Setup

```bash
cd fin-analysis-api

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Generate SSL certificates
openssl req -x509 -newkey rsa:4096 -nodes \
  -out cert.pem -keyout key.pem -days 365 \
  -subj "/CN=localhost"

# Create .env file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

### Frontend Setup

```bash
cd fin-analysis-app

# Install dependencies
npm install

# Create .env (if needed)
cp .env.example .env
```

### IDE Configuration

#### VS Code

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- ESLint
- Prettier
- React Developer Tools

**Settings (.vscode/settings.json):**
```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm

- Enable FastAPI support
- Configure Python interpreter to use venv
- Set up automatic import optimization
- Enable type checking

---

## Code Structure

### Backend Structure

```
fin-analysis-api/
├── main.py                  # Application entry point
├── config.py                # Settings and configuration
├── cert.pem / key.pem       # SSL certificates
├── routers/
│   ├── __init__.py
│   ├── financial_data.py    # Financial metrics endpoints
│   └── schwab_oauth.py      # Schwab OAuth endpoints
├── services/
│   ├── __init__.py
│   ├── exceptions.py        # Custom exception classes
│   ├── financial_data_service.py  # Unified service
│   ├── alphavantage_service.py
│   ├── yfinance_service.py
│   ├── polygon_service.py
│   ├── schwab_service.py
│   └── token_manager.py
└── schwab_tokens/           # Encrypted OAuth tokens
```

### Frontend Structure

```
fin-analysis-app/
├── public/
├── src/
│   ├── App.jsx              # Main component
│   ├── App.css              # Global styles
│   ├── main.jsx             # React entry point
│   ├── components/
│   │   ├── SchwabConnect.jsx
│   │   ├── SchwabQuote.jsx
│   │   ├── MetricsDisplay.jsx
│   │   ├── LoadingSpinner.jsx
│   │   └── SnackbarProvider.jsx
│   └── services/
│       ├── api.js           # Financial API client
│       └── schwabApi.js     # Schwab API client
└── package.json
```

---

## Adding New Features

### Adding a New Data Provider

1. **Create Provider Service** (`services/new_provider_service.py`):

```python
import requests
from typing import Optional, Dict, Any
from services.exceptions import RateLimitError, DataNotFoundError, FinancialDataError

class NewProviderService:
    """Service for NewProvider API."""

    def __init__(self):
        self.api_key = settings.new_provider_api_key
        self.base_url = "https://api.newprovider.com"

    def get_financials(
        self,
        ticker: str,
        timeframe: str = "annual",
        limit: int = 1
    ) -> Optional[list]:
        try:
            # Make API call
            response = requests.get(
                f"{self.base_url}/financials/{ticker}",
                params={"apikey": self.api_key},
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            if not data.get("results"):
                raise DataNotFoundError(
                    f"No data for {ticker}",
                    provider="newprovider"
                )

            return data["results"]

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                raise RateLimitError(
                    "Rate limit exceeded",
                    provider="newprovider",
                    original_error=e
                )
            # Handle other errors...
            raise FinancialDataError(
                str(e),
                provider="newprovider",
                original_error=e
            )

    def extract_income_statement(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract and transform income statement
        return {
            "date": data.get("date"),
            "revenues": data.get("revenue"),
            "operating_income": data.get("operating_income"),
            # ...
        }

    def extract_balance_sheet(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Extract and transform balance sheet
        return {
            "assets": data.get("total_assets"),
            "liabilities": data.get("total_liabilities"),
            # ...
        }

# Create singleton instance
new_provider_service = NewProviderService()
```

2. **Update Financial Data Service** (`services/financial_data_service.py`):

```python
from services.new_provider_service import new_provider_service

ProviderType = Literal["polygon", "yfinance", "alphavantage", "newprovider"]

class FinancialDataService:
    def __init__(self):
        self.polygon = polygon_service
        self.yfinance = yfinance_service
        self.alphavantage = alphavantage_service
        self.newprovider = new_provider_service  # Add new provider

    def _get_service(self, provider: Optional[str] = None):
        # ...
        elif provider_lower == "newprovider":
            if not settings.has_new_provider_key:
                print("Warning: NewProvider requested but no API key.")
                return self.yfinance
            return self.newprovider
        # ...
```

3. **Update Configuration** (`config.py`):

```python
class Settings(BaseSettings):
    # ...
    new_provider_api_key: Optional[str] = None

    @property
    def has_new_provider_key(self) -> bool:
        return bool(self.new_provider_api_key)
```

4. **Update Environment** (`.env.example`):

```bash
NEW_PROVIDER_API_KEY=your_api_key_here
```

### Adding a New Financial Metric

1. **Add Calculation Function** (`routers/financial_data.py`):

```python
def calculate_debt_to_equity(
    total_debt: float,
    equity: float
) -> Optional[float]:
    """
    Calculate Debt to Equity Ratio.

    Formula: Total Debt / Equity

    Args:
        total_debt: Total debt
        equity: Shareholder equity

    Returns:
        Debt to equity ratio or None if invalid
    """
    if not equity or equity == 0:
        return None
    return total_debt / equity
```

2. **Update Response Model** (`routers/financial_data.py`):

```python
class StockMetrics(BaseModel):
    # ... existing fields ...

    # Debt to Equity
    debt_to_equity: Optional[float] = None
    debt_to_equity_percent: Optional[str] = None
```

3. **Calculate in Endpoint** (`routers/financial_data.py`):

```python
@router.get("/metrics/{ticker}", response_model=StockMetrics)
async def get_stock_metrics(...):
    # ... existing code ...

    # Calculate Debt to Equity
    debt_to_equity = calculate_debt_to_equity(total_debt, equity)

    return StockMetrics(
        # ... existing fields ...
        debt_to_equity=debt_to_equity,
        debt_to_equity_percent=f"{debt_to_equity * 100:.2f}%" if debt_to_equity else None,
        # ...
    )
```

4. **Display in Frontend** (`components/MetricsDisplay.jsx`):

```jsx
{metrics.debt_to_equity && (
  <div className="metric-card">
    <h3>Debt to Equity</h3>
    <p className="metric-value">{metrics.debt_to_equity_percent}</p>
  </div>
)}
```

### Adding a New Endpoint

1. **Create Endpoint** (`routers/financial_data.py`):

```python
@router.get("/compare/{ticker1}/{ticker2}", response_model=dict)
async def compare_stocks(
    ticker1: str,
    ticker2: str,
    timeframe: str = Query(default="annual", pattern="^(annual|quarterly)$")
):
    """
    Compare financial metrics between two stocks.
    """
    try:
        metrics1 = await get_stock_metrics(ticker1, timeframe)
        metrics2 = await get_stock_metrics(ticker2, timeframe)

        return {
            "ticker1": ticker1,
            "ticker2": ticker2,
            "metrics1": metrics1,
            "metrics2": metrics2,
            "comparison": {
                "roce_diff": metrics1.roce - metrics2.roce,
                # ... other comparisons
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

2. **Create Frontend API Function** (`services/api.js`):

```javascript
export const compareStocks = async (ticker1, ticker2, timeframe = 'annual') => {
  try {
    const response = await fetch(
      `${API_BASE_URL}/compare/${ticker1}/${ticker2}?timeframe=${timeframe}`
    );

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail);
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};
```

3. **Create Frontend Component** (`components/StockComparison.jsx`):

```jsx
import { useState } from 'react';
import { compareStocks } from '../services/api';

export default function StockComparison() {
  const [ticker1, setTicker1] = useState('');
  const [ticker2, setTicker2] = useState('');
  const [comparison, setComparison] = useState(null);

  const handleCompare = async () => {
    try {
      const data = await compareStocks(ticker1, ticker2);
      setComparison(data);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      <input value={ticker1} onChange={(e) => setTicker1(e.target.value)} />
      <input value={ticker2} onChange={(e) => setTicker2(e.target.value)} />
      <button onClick={handleCompare}>Compare</button>

      {comparison && (
        <div>
          {/* Display comparison results */}
        </div>
      )}
    </div>
  );
}
```

---

## Error Handling Patterns

### Creating Custom Exceptions

All custom exceptions inherit from `FinancialDataError`:

```python
# services/exceptions.py

class FinancialDataError(Exception):
    """Base exception for financial data errors."""

    def __init__(
        self,
        message: str,
        provider: str = None,
        original_error: Exception = None
    ):
        self.message = message
        self.provider = provider
        self.original_error = original_error
        super().__init__(self.message)

class RateLimitError(FinancialDataError):
    """Exception raised when API rate limit is exceeded."""
    pass

class DataNotFoundError(FinancialDataError):
    """Exception raised when no data is found for a ticker."""
    pass

class APIKeyError(FinancialDataError):
    """Exception raised when API key is invalid or missing."""
    pass
```

### Raising Exceptions in Services

```python
# In provider services
try:
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    if not response.json().get("results"):
        raise DataNotFoundError(
            f"No data for {ticker}",
            provider="myservice"
        )

except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        raise APIKeyError(
            "Invalid API key",
            provider="myservice",
            original_error=e
        )
    elif e.response.status_code == 429:
        raise RateLimitError(
            "Rate limit exceeded",
            provider="myservice",
            original_error=e
        )
    else:
        raise FinancialDataError(
            f"HTTP {e.response.status_code}",
            provider="myservice",
            original_error=e
        )
```

### Handling Exceptions in Routers

```python
# In routers
try:
    result = financial_data_service.get_financials(ticker)
    # ... process result

except RateLimitError as e:
    raise HTTPException(
        status_code=429,
        detail=f"{e.message} (Provider: {e.provider})"
    )
except APIKeyError as e:
    raise HTTPException(
        status_code=401,
        detail=f"{e.message} (Provider: {e.provider})"
    )
except DataNotFoundError as e:
    raise HTTPException(
        status_code=404,
        detail=f"{e.message} (Provider: {e.provider})"
    )
except FinancialDataError as e:
    raise HTTPException(
        status_code=500,
        detail=f"{e.message} (Provider: {e.provider})"
    )
```

### Frontend Error Handling

```javascript
try {
  const data = await getStockMetrics(ticker);
  setMetrics(data);
} catch (err) {
  // Error message already includes provider context
  setError(err.message);
}
```

---

## Testing

### Backend Unit Tests

Create `tests/test_financial_data_service.py`:

```python
import pytest
from services.financial_data_service import financial_data_service
from services.exceptions import DataNotFoundError, RateLimitError

def test_get_financials_success():
    """Test successful financial data retrieval."""
    result, provider = financial_data_service.get_financials("AAPL")
    assert result is not None
    assert provider in ["yfinance", "alphavantage", "polygon"]

def test_get_financials_invalid_ticker():
    """Test invalid ticker raises DataNotFoundError."""
    with pytest.raises(DataNotFoundError):
        financial_data_service.get_financials("INVALIDTICKER")

def test_fallback_logic():
    """Test fallback to yfinance when primary provider fails."""
    # Mock alphavantage failure
    result, provider = financial_data_service.get_financials(
        "AAPL",
        provider="alphavantage"
    )
    # Should fallback to yfinance
    assert provider == "yfinance"
```

Run tests:
```bash
cd fin-analysis-api
pytest tests/
```

### Frontend Tests

Create `src/components/__tests__/MetricsDisplay.test.jsx`:

```javascript
import { render, screen } from '@testing-library/react';
import MetricsDisplay from '../MetricsDisplay';

describe('MetricsDisplay', () => {
  const mockMetrics = {
    ticker: 'AAPL',
    roce_percent: '58.44%',
    earnings_yield_percent: '4.21%',
  };

  test('renders metrics correctly', () => {
    render(<MetricsDisplay metrics={mockMetrics} />);

    expect(screen.getByText('AAPL')).toBeInTheDocument();
    expect(screen.getByText('58.44%')).toBeInTheDocument();
    expect(screen.getByText('4.21%')).toBeInTheDocument();
  });

  test('displays notes when provided', () => {
    const metricsWithNotes = {
      ...mockMetrics,
      notes: ['Test note 1', 'Test note 2']
    };

    render(<MetricsDisplay metrics={metricsWithNotes} />);

    expect(screen.getByText('Test note 1')).toBeInTheDocument();
    expect(screen.getByText('Test note 2')).toBeInTheDocument();
  });
});
```

Run tests:
```bash
cd fin-analysis-app
npm test
```

### Integration Tests

```python
# tests/test_api_integration.py
import requests

BASE_URL = "https://127.0.0.1:8000/api/v1"

def test_health_endpoint():
    response = requests.get(f"{BASE_URL}/health", verify=False)
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_metrics_endpoint():
    response = requests.get(
        f"{BASE_URL}/metrics/AAPL",
        verify=False
    )
    assert response.status_code == 200
    data = response.json()
    assert data["ticker"] == "AAPL"
    assert "roce" in data
    assert "earnings_yield" in data
```

---

## Deployment

### Environment Variables for Production

**DO NOT** hardcode production URLs. Use environment variables:

```bash
# Production .env
FRONTEND_URL=https://yourdomain.com
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
ALPHA_VANTAGE_API_KEY=prod_api_key
```

### Docker Deployment

Create `Dockerfile` for backend:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Generate SSL cert or mount volume
RUN openssl req -x509 -newkey rsa:4096 -nodes \
    -out cert.pem -keyout key.pem -days 365 \
    -subj "/CN=api.yourdomain.com"

EXPOSE 8000

CMD ["python", "main.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  api:
    build: ./fin-analysis-api
    ports:
      - "8000:8000"
    environment:
      - FRONTEND_URL=${FRONTEND_URL}
      - CORS_ORIGINS=${CORS_ORIGINS}
      - ALPHA_VANTAGE_API_KEY=${ALPHA_VANTAGE_API_KEY}
    volumes:
      - ./schwab_tokens:/app/schwab_tokens

  frontend:
    build: ./fin-analysis-app
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=${API_BASE_URL}
```

---

## Best Practices

### Python Code Style

- Use type hints
- Follow PEP 8
- Max line length: 100 characters
- Use docstrings for all functions
- Organize imports: stdlib, third-party, local

```python
from typing import Optional, Dict, Any  # Type hints

def calculate_roce(
    operating_income: float,
    total_assets: float,
    current_liabilities: float
) -> Optional[float]:
    """
    Calculate Return on Capital Employed.

    Args:
        operating_income: Operating income (EBIT)
        total_assets: Total assets
        current_liabilities: Current liabilities

    Returns:
        ROCE as decimal or None if invalid
    """
    capital_employed = total_assets - current_liabilities

    if capital_employed == 0:
        return None

    return operating_income / capital_employed
```

### JavaScript/React Style

- Use functional components
- Destructure props
- Use meaningful variable names
- Handle loading and error states
- Use async/await

```javascript
export default function MetricsDisplay({ metrics, loading, error }) {
  if (loading) return <LoadingSpinner />;
  if (error) return <ErrorMessage message={error} />;
  if (!metrics) return null;

  const { ticker, roce_percent, earnings_yield_percent } = metrics;

  return (
    <div className="metrics-container">
      <h2>{ticker}</h2>
      <p>ROCE: {roce_percent}</p>
      <p>Earnings Yield: {earnings_yield_percent}</p>
    </div>
  );
}
```

### Configuration Management

- **NEVER** hardcode URLs or secrets
- Use environment variables for all configuration
- Provide `.env.example` templates
- Document all environment variables
- Use type-safe settings (Pydantic)

### Error Messages

- Be specific and actionable
- Include provider context
- Suggest next steps
- Use appropriate HTTP status codes

Good:
```
"Yahoo Finance rate limit exceeded. Please wait a few minutes and try again.
Consider using a different provider (alphavantage) if this persists. (Provider: yfinance)"
```

Bad:
```
"Error fetching data"
```

### Git Commits

- Write descriptive commit messages
- Use conventional commits format
- Reference issues when applicable

```bash
git commit -m "feat: add debt-to-equity ratio calculation

- Add calculation function in routers/financial_data.py
- Update StockMetrics response model
- Display in MetricsDisplay component

Closes #123"
```

---

*Last Updated: 2025-12-11*

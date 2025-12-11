# API Testing Guide

This guide provides examples for testing the Financial Analysis Dashboard API endpoints.

## Prerequisites

- Backend server running at `https://127.0.0.1:8000`
- SSL certificate accepted in browser
- curl or similar HTTP client installed

## Base URL

```
https://127.0.0.1:8000/api/v1
```

**Note**: Use `-k` flag with curl to bypass SSL certificate verification (self-signed cert).

---

## Health Check

### Basic Health Check

```bash
curl -k https://127.0.0.1:8000/api/v1/health
```

**Expected Response:**
```json
{
  "status": "healthy",
  "service": "Financial Data API",
  "provider": "Yahoo Finance (yfinance)"
}
```

---

## Financial Metrics Endpoints

### Get Stock Metrics (Default Provider)

```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL" | python -m json.tool
```

**Expected Response:**
```json
{
  "ticker": "AAPL",
  "date": "2023-09-30",
  "period": "annual",
  "roce": 0.5844,
  "roce_percent": "58.44%",
  "working_capital": 1234567890,
  "capital_employed": 9876543210,
  "earnings_yield": 0.0421,
  "earnings_yield_percent": "4.21%",
  "ebit": 119437000000,
  "enterprise_value": 2845621000000,
  "market_cap": 2891234000000,
  "stock_price": 185.92,
  "shares_outstanding": 15552799744,
  "total_debt": 123456789000,
  "cash_and_equivalents": 29965000000,
  "total_assets": 352755000000,
  "current_liabilities": 145308000000,
  ...
}
```

### Get Metrics with Specific Provider

**Yahoo Finance:**
```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/MSFT?provider=yfinance" | python -m json.tool
```

**Alpha Vantage:**
```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/GOOGL?provider=alphavantage" | python -m json.tool
```

**Polygon:**
```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/TSLA?provider=polygon" | python -m json.tool
```

### Get Quarterly Metrics

```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?timeframe=quarterly" | python -m json.tool
```

### Combine Parameters

```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/NVDA?timeframe=quarterly&provider=alphavantage" | python -m json.tool
```

---

## Financial Statements Endpoint

### Get Financial Data (1 Period)

```bash
curl -k "https://127.0.0.1:8000/api/v1/financials/AAPL" | python -m json.tool
```

**Expected Response:**
```json
{
  "ticker": "AAPL",
  "date": "2023-09-30",
  "fiscal_year": "2023",
  "fiscal_period": "FY",
  "revenues": 383285000000,
  "operating_income": 114301000000,
  "net_income": 96995000000,
  "cost_of_revenue": 214137000000,
  "gross_profit": 169148000000,
  "operating_expenses": 54847000000,
  "current_assets": 143566000000,
  "current_liabilities": 145308000000,
  "fixed_assets": 43715000000,
  "total_assets": 352755000000,
  "total_liabilities": 290437000000,
  "equity": 62318000000,
  "working_capital": -1742000000,
  "roce": 0.5508,
  "roce_percent": "55.08%"
}
```

### Get Multiple Periods

```bash
curl -k "https://127.0.0.1:8000/api/v1/financials/MSFT?limit=3" | python -m json.tool
```

### Quarterly Financials

```bash
curl -k "https://127.0.0.1:8000/api/v1/financials/TSLA?timeframe=quarterly&limit=4" | python -m json.tool
```

---

## Error Testing

### Invalid Ticker

```bash
curl -k "https://127.0.0.1:8000/api/v1/metrics/INVALIDTICKER" | python -m json.tool
```

**Expected Response (404):**
```json
{
  "detail": "No financial data available for ticker INVALIDTICKER. The ticker may be invalid or data is not available from Yahoo Finance. (Provider: yfinance)"
}
```

### Rate Limit Error (Alpha Vantage)

```bash
# After exceeding 25 requests/day on Alpha Vantage
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=alphavantage" | python -m json.tool
```

**Expected Response (429):**
```json
{
  "detail": "Alpha Vantage API rate limit exceeded (25 requests/day). Please try again tomorrow or use a different provider. (Provider: alphavantage)"
}
```

### Rate Limit Error (Yahoo Finance)

```bash
# After Yahoo Finance rate limiting kicks in
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL" | python -m json.tool
```

**Expected Response (429):**
```json
{
  "detail": "Yahoo Finance rate limit exceeded. Please wait a few minutes and try again. Consider using a different provider (alphavantage) if this persists. (Provider: yfinance)"
}
```

---

## Schwab OAuth Endpoints

### Check Connection Status

```bash
curl -k https://127.0.0.1:8000/api/v1/oauth/status | python -m json.tool
```

**Expected Response (Not Connected):**
```json
{
  "connected": false,
  "has_valid_access_token": false,
  "has_valid_refresh_token": false
}
```

**Expected Response (Connected):**
```json
{
  "connected": true,
  "has_valid_access_token": true,
  "has_valid_refresh_token": true
}
```

### Get Authorization URL

```bash
curl -k https://127.0.0.1:8000/api/v1/oauth/connect | python -m json.tool
```

**Expected Response:**
```json
{
  "auth_url": "https://api.schwabapi.com/v1/oauth/authorize?response_type=code&client_id=...&redirect_uri=..."
}
```

### Get Stock Quote (Requires Schwab Connection)

```bash
curl -k "https://127.0.0.1:8000/api/v1/oauth/quote/AAPL" | python -m json.tool
```

**Expected Response (Connected):**
```json
{
  "symbol": "AAPL",
  "quote": {
    "lastPrice": 185.92,
    "totalVolume": 48567890,
    "52WkHigh": 199.62,
    "52WkLow": 164.08,
    "peRatio": 29.45,
    "divYield": 0.52,
    "eps": 6.31
  }
}
```

**Expected Response (Not Connected - 401):**
```json
{
  "detail": "Not connected to Schwab. Please authenticate first."
}
```

### Disconnect from Schwab

```bash
curl -k -X POST https://127.0.0.1:8000/api/v1/oauth/disconnect | python -m json.tool
```

**Expected Response:**
```json
{
  "message": "Successfully disconnected from Schwab"
}
```

---

## Using Python Requests

### Basic Example

```python
import requests
import json

# Disable SSL warnings (self-signed cert)
requests.packages.urllib3.disable_warnings()

# Get stock metrics
response = requests.get(
    "https://127.0.0.1:8000/api/v1/metrics/AAPL",
    verify=False  # Skip SSL verification
)

if response.status_code == 200:
    data = response.json()
    print(json.dumps(data, indent=2))
else:
    print(f"Error {response.status_code}: {response.json()}")
```

### With Parameters

```python
import requests
import json

requests.packages.urllib3.disable_warnings()

params = {
    "timeframe": "quarterly",
    "provider": "alphavantage"
}

response = requests.get(
    "https://127.0.0.1:8000/api/v1/metrics/MSFT",
    params=params,
    verify=False
)

print(json.dumps(response.json(), indent=2))
```

### Error Handling

```python
import requests

requests.packages.urllib3.disable_warnings()

try:
    response = requests.get(
        "https://127.0.0.1:8000/api/v1/metrics/AAPL",
        verify=False,
        timeout=10
    )
    response.raise_for_status()

    data = response.json()
    print(f"ROCE: {data['roce_percent']}")
    print(f"Earnings Yield: {data['earnings_yield_percent']}")

except requests.exceptions.HTTPError as e:
    if response.status_code == 429:
        print("Rate limit exceeded!")
    elif response.status_code == 404:
        print("Ticker not found!")
    else:
        print(f"HTTP Error: {e}")
    print(f"Details: {response.json()['detail']}")

except requests.exceptions.RequestException as e:
    print(f"Request failed: {e}")
```

---

## Using JavaScript/Fetch

### Basic Example

```javascript
async function getMetrics(ticker) {
  try {
    const response = await fetch(
      `https://127.0.0.1:8000/api/v1/metrics/${ticker}`
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail);
    }

    const data = await response.json();
    console.log('ROCE:', data.roce_percent);
    console.log('Earnings Yield:', data.earnings_yield_percent);

    return data;
  } catch (error) {
    console.error('Failed to fetch metrics:', error.message);
    throw error;
  }
}

// Usage
getMetrics('AAPL');
```

### With Parameters

```javascript
async function getQuarterlyMetrics(ticker, provider) {
  const params = new URLSearchParams({
    timeframe: 'quarterly',
    provider: provider || 'yfinance'
  });

  const url = `https://127.0.0.1:8000/api/v1/metrics/${ticker}?${params}`;

  try {
    const response = await fetch(url);

    if (!response.ok) {
      const error = await response.json();

      // Handle specific error types
      if (response.status === 429) {
        console.warn('Rate limit exceeded:', error.detail);
      } else if (response.status === 404) {
        console.error('Ticker not found:', error.detail);
      }

      throw new Error(error.detail);
    }

    return await response.json();
  } catch (error) {
    console.error('Error:', error.message);
    throw error;
  }
}

// Usage
getQuarterlyMetrics('MSFT', 'alphavantage');
```

---

## Interactive API Documentation

FastAPI provides interactive API documentation:

1. **Swagger UI**: `https://127.0.0.1:8000/docs`
2. **ReDoc**: `https://127.0.0.1:8000/redoc`

Both interfaces allow you to:
- View all endpoints
- See request/response schemas
- Test endpoints directly in the browser
- Download OpenAPI specification

---

## Common Test Scenarios

### Scenario 1: Compare Providers

```bash
# Test same ticker with different providers
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=yfinance" > yfinance.json
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=alphavantage" > alphavantage.json

# Compare results
diff yfinance.json alphavantage.json
```

### Scenario 2: Test Fallback Logic

```bash
# Request from Alpha Vantage (may fallback to yfinance on error)
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=alphavantage" | python -m json.tool
```

### Scenario 3: Batch Testing Multiple Tickers

```bash
#!/bin/bash
TICKERS=("AAPL" "MSFT" "GOOGL" "TSLA" "NVDA")

for ticker in "${TICKERS[@]}"; do
  echo "Testing $ticker..."
  curl -k "https://127.0.0.1:8000/api/v1/metrics/$ticker" | python -m json.tool > "${ticker}_metrics.json"
  echo "Saved to ${ticker}_metrics.json"
done
```

### Scenario 4: Performance Testing

```bash
# Time the API response
time curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL" > /dev/null 2>&1
```

---

## Troubleshooting Tips

### Issue: SSL Certificate Error

**Error:**
```
curl: (60) SSL certificate problem: self signed certificate
```

**Solution:**
```bash
# Use -k flag to skip certificate verification
curl -k https://127.0.0.1:8000/api/v1/health
```

### Issue: Connection Refused

**Error:**
```
curl: (7) Failed to connect to 127.0.0.1 port 8000: Connection refused
```

**Solution:**
- Ensure backend server is running: `python main.py`
- Check if port 8000 is in use: `lsof -i:8000`

### Issue: Empty Response

**Possible Causes:**
1. Server crashed - check server logs
2. Rate limit exceeded - wait or change provider
3. Invalid ticker symbol - verify ticker is correct

### Issue: Timeout

```bash
# Increase timeout
curl -k --max-time 30 "https://127.0.0.1:8000/api/v1/metrics/AAPL"
```

---

## Advanced Testing

### Load Testing with Apache Bench

```bash
# Install ab (Apache Bench)
# macOS: brew install httpd
# Linux: sudo apt-get install apache2-utils

# Run 100 requests with 10 concurrent
ab -n 100 -c 10 -k "https://127.0.0.1:8000/api/v1/health"
```

### Automated Testing Script

```bash
#!/bin/bash

echo "=== Financial Analysis API Test Suite ==="

# Test 1: Health Check
echo -e "\n[Test 1] Health Check..."
curl -k -s https://127.0.0.1:8000/api/v1/health | python -m json.tool && echo "✓ PASSED" || echo "✗ FAILED"

# Test 2: Valid Ticker
echo -e "\n[Test 2] Valid Ticker (AAPL)..."
curl -k -s "https://127.0.0.1:8000/api/v1/metrics/AAPL" | python -m json.tool > /dev/null && echo "✓ PASSED" || echo "✗ FAILED"

# Test 3: Invalid Ticker
echo -e "\n[Test 3] Invalid Ticker..."
response=$(curl -k -s -w "%{http_code}" "https://127.0.0.1:8000/api/v1/metrics/INVALID")
[[ "$response" == *"404"* ]] && echo "✓ PASSED" || echo "✗ FAILED"

# Test 4: Quarterly Timeframe
echo -e "\n[Test 4] Quarterly Timeframe..."
curl -k -s "https://127.0.0.1:8000/api/v1/metrics/MSFT?timeframe=quarterly" | python -m json.tool > /dev/null && echo "✓ PASSED" || echo "✗ FAILED"

echo -e "\n=== Test Suite Complete ==="
```

---

*Last Updated: 2025-12-11*

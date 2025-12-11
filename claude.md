# Financial Analysis Dashboard - Project Documentation

## Project Overview

A full-stack financial analysis application that provides stock market data, financial metrics calculations (ROCE, Earnings Yield), and real-time quotes. The application integrates with multiple data providers (Schwab, Yahoo Finance, Alpha Vantage, Polygon) and features OAuth 2.0 authentication for Schwab API access.

**Tech Stack:**
- **Backend**: FastAPI (Python) with HTTPS/SSL
- **Frontend**: React with Material-UI
- **Authentication**: OAuth 2.0 (Schwab Developer API)
- **Data Providers**: Schwab, Yahoo Finance (yfinance), Alpha Vantage, Polygon.io

---

## Project Structure

```
fin-analysis/
├── fin-analysis-api/          # FastAPI backend
│   ├── main.py                # Application entry point
│   ├── config.py              # Settings and environment configuration
│   ├── cert.pem / key.pem     # Self-signed SSL certificates for HTTPS
│   ├── routers/
│   │   ├── financial_data.py  # Financial metrics endpoints
│   │   └── schwab_oauth.py    # Schwab OAuth endpoints
│   ├── services/
│   │   ├── exceptions.py      # Custom exception classes
│   │   ├── financial_data_service.py  # Unified service with fallback logic
│   │   ├── alphavantage_service.py
│   │   ├── yfinance_service.py
│   │   ├── polygon_service.py
│   │   ├── schwab_service.py  # OAuth flow and Schwab API calls
│   │   └── token_manager.py   # Encrypted token storage (Fernet)
│   └── .env                   # Environment variables (API keys, URLs)
│
└── fin-analysis-app/          # React frontend
    ├── src/
    │   ├── App.jsx            # Main application component
    │   ├── App.css            # Application styles
    │   ├── components/
    │   │   ├── SchwabConnect.jsx    # OAuth connection status
    │   │   ├── SchwabQuote.jsx      # Real-time quote display
    │   │   ├── SnackbarProvider.jsx # Toast notifications
    │   │   ├── MetricsDisplay.jsx
    │   │   └── LoadingSpinner.jsx
    │   └── services/
    │       ├── api.js         # Financial metrics API client
    │       └── schwabApi.js   # Schwab API client
    └── .env                   # Frontend environment variables
```

---

## Key Features

### 1. Schwab OAuth 2.0 Integration
- **OAuth Flow**: Authorization code flow with encrypted token storage
- **Token Management**: Automatic refresh when <5 minutes remaining
- **Encryption**: Fernet symmetric encryption for stored tokens
- **Real-time Quotes**: Stock price, volume, 52-week range, P/E ratio, dividend yield, EPS

### 2. Financial Metrics Analysis
- **ROCE (Return on Capital Employed)**: `Operating Income / (Total Assets - Current Liabilities)`
- **Earnings Yield**: `EBIT / Enterprise Value`
- **Working Capital**: Current Assets - Current Liabilities
- **Enterprise Value**: Market Cap + Total Debt - Cash

### 3. Multi-Provider Architecture
- **Provider Priority**: yfinance > alphavantage > polygon (for personal use)
- **Automatic Fallback**: Configurable fallback to yfinance on errors
- **Provider Selection**: Optional provider override via API query parameter

### 4. Comprehensive Error Handling
- **Custom Exceptions**: RateLimitError, DataNotFoundError, APIKeyError, FinancialDataError
- **HTTP Status Codes**: 429 (rate limit), 401 (auth), 404 (not found), 500 (server error)
- **Transparent Errors**: All errors include provider name and actionable messages
- **Provider-Specific Logic**:
  - Alpha Vantage: Detects 25 requests/day limit
  - Yahoo Finance: Detects JSONDecodeError as rate limiting (429)
  - Polygon: Parses HTTP status codes from API responses

---

## Environment Configuration

### Backend (.env)
```bash
# Schwab OAuth
SCHWAB_APP_KEY=<your_app_key>
SCHWAB_APP_SECRET=<your_app_secret>
SCHWAB_REDIRECT_URI=https://127.0.0.1:8000/api/v1/oauth/callback
SCHWAB_ENCRYPTION_KEY=<generated_fernet_key>

# API Keys
ALPHA_VANTAGE_API_KEY=<your_api_key>
POLYGON_API_KEY=<your_api_key>  # Optional

# URLs (NO hardcoded defaults in config.py)
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8000

# Provider Settings
DEFAULT_PROVIDER=yfinance  # Optional: yfinance, alphavantage, polygon
ENABLE_FALLBACK=true
```

### Frontend (.env)
```bash
VITE_API_BASE_URL=https://127.0.0.1:8000
```

**Important**: All environment-specific configuration must be in `.env` files. No hardcoded URLs or defaults in `config.py`.

---

## API Endpoints

### Financial Data

**GET** `/api/v1/financials/{ticker}`
- Query params: `timeframe` (annual/quarterly), `limit` (1-10), `provider` (optional)
- Returns: Income statement, balance sheet, working capital, ROCE

**GET** `/api/v1/metrics/{ticker}`
- Query params: `timeframe` (annual/quarterly), `provider` (optional)
- Returns: ROCE, Earnings Yield, Enterprise Value, all components

**GET** `/api/v1/health`
- Health check endpoint

### Schwab OAuth

**GET** `/api/v1/oauth/connect`
- Initiates OAuth flow, returns Schwab authorization URL

**GET** `/api/v1/oauth/callback`
- Receives authorization code, exchanges for tokens, redirects to frontend

**GET** `/api/v1/oauth/status`
- Returns connection status and token validity

**POST** `/api/v1/oauth/disconnect`
- Deletes stored tokens

**GET** `/api/v1/oauth/quote/{symbol}`
- Returns real-time quote from Schwab API

**TODO**: Rename router prefix from `/api/v1/oauth` to `/api/v1/schwab` after updating redirect URI in Schwab Developer Portal (waiting period applies).

---

## Data Providers

### Yahoo Finance (yfinance)
- **Type**: Free, unlimited (reasonable use)
- **Data**: Financials, balance sheets, market data
- **Limitations**: Rate limiting (429 errors), JSONDecodeError on rate limit
- **Error Detection**: Checks for "expecting value" as rate limit indicator

### Alpha Vantage
- **Type**: Free tier (25 requests/day), paid premium tiers
- **Data**: Income statements, balance sheets
- **Limitations**: 25 API calls per day on free tier
- **Error Detection**: Checks error messages for "rate limit", "premium", "25 requests"

### Polygon.io
- **Type**: Requires API key, multiple tier options
- **Data**: Comprehensive financials, ratios, market data
- **Limitations**: Rate limits based on subscription tier
- **Error Detection**: HTTP status code parsing (401, 429, 404)

### Schwab Developer API
- **Type**: OAuth 2.0 authentication required
- **Data**: Real-time quotes, market data
- **Authentication**: HTTP Basic Auth for token exchange
- **Endpoints**: `/{symbol}/quotes` (not `/quotes/{symbol}`)

---

## Error Handling System

### Custom Exception Hierarchy
```python
FinancialDataError (base)
├── RateLimitError      # HTTP 429
├── APIKeyError         # HTTP 401
└── DataNotFoundError   # HTTP 404
```

### Error Flow
1. **Service Layer**: Raises specific exception with provider context
2. **Financial Data Service**: Catches exceptions, attempts fallback (except RateLimitError/APIKeyError)
3. **Router Layer**: Maps exceptions to HTTP status codes with detailed messages
4. **Frontend**: Displays error with provider information

### Example Error Messages
```
"Alpha Vantage API rate limit exceeded (25 requests/day).
Please try again tomorrow or use a different provider. (Provider: alphavantage)"

"Yahoo Finance rate limit exceeded. Please wait a few minutes and try again.
Consider using a different provider (alphavantage) if this persists. (Provider: yfinance)"

"Polygon API rate limit exceeded. Please upgrade your plan or wait before retrying.
(Provider: polygon)"
```

---

## Authentication & Security

### Schwab OAuth 2.0 Flow
1. User clicks "Connect to Schwab"
2. Backend generates authorization URL → Frontend redirects to Schwab
3. User authenticates at Schwab → Schwab redirects to callback with `code`
4. Backend exchanges code for tokens using HTTP Basic Auth
5. Tokens encrypted with Fernet and saved to `schwab_tokens/tokens.enc`
6. Frontend receives success redirect with `?schwab=connected`

### Token Management
- **Access Token**: ~30 minutes validity
- **Refresh Token**: ~7 days validity
- **Proactive Refresh**: When <5 minutes remaining on access token
- **Encryption**: Fernet symmetric encryption (`cryptography` library)
- **Storage**: `schwab_tokens/tokens.enc` (single-user for now)

### SSL/HTTPS
- **Development**: Self-signed certificates (`cert.pem`, `key.pem`)
- **Generated with**: `openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365`
- **Browser**: Must accept self-signed certificate exception
- **Required**: Schwab OAuth requires HTTPS redirect URI

---

## Known Issues & Solutions

### Yahoo Finance "Expecting value" Error
- **Cause**: Yahoo returns 429 HTML error page, yfinance tries to parse as JSON
- **Solution**: Detect JSONDecodeError as rate limit indicator
- **Workaround**: Use `provider=alphavantage` query parameter

### Alpha Vantage Rate Limit
- **Limit**: 25 requests/day on free tier
- **Detection**: Error messages contain "rate limit", "premium", or "25 requests"
- **Workaround**: Wait until next day or use different provider

### Schwab Callback Path Mismatch
- **Issue**: Router prefix must match registered redirect URI exactly
- **Current**: `/api/v1/oauth/callback` (matches Schwab registration)
- **Future**: Rename to `/api/v1/schwab/callback` after Schwab waiting period

### Schwab Quote Endpoint
- **Correct**: `/{symbol}/quotes`
- **Incorrect**: `/quotes/{symbol}`
- **Fixed**: Updated to correct path in `schwab_service.py`

---

## Development Setup

### Backend
```bash
cd fin-analysis-api
pip install -r requirements.txt
pip install cryptography  # If not in requirements.txt

# Generate SSL certificates (if needed)
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Create .env file with required variables
# Start server
python main.py
```

Server runs on: `https://127.0.0.1:8000`

### Frontend
```bash
cd fin-analysis-app
npm install

# Create .env file with VITE_API_BASE_URL
# Start dev server
npm run dev
```

App runs on: `http://localhost:5173`

---

## Testing

### Test Financial Metrics
```bash
# Using default provider (yfinance)
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL"

# Using specific provider
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=alphavantage"

# With timeframe
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?timeframe=quarterly"
```

### Test Error Handling
```bash
# Test invalid ticker
curl -k "https://127.0.0.1:8000/api/v1/metrics/INVALIDTICKER"

# Test rate limit (if applicable)
curl -k "https://127.0.0.1:8000/api/v1/metrics/AAPL?provider=alphavantage"
```

### Test Schwab OAuth
1. Navigate to frontend: `http://localhost:5173`
2. Click "Connect to Schwab"
3. Authenticate with Schwab credentials
4. Verify redirect back to app with success message
5. Test quote retrieval with stock symbol

---

## Future Enhancements

### Multi-User Support
- Current: Single user, tokens in `schwab_tokens/tokens.enc`
- Future: Database storage with user-specific token management

### Router Naming
- Rename `/api/v1/oauth` → `/api/v1/schwab`
- Update Schwab redirect URI registration
- Wait for Schwab's redirect URI change waiting period

### Provider Improvements
- Add more data providers
- Implement request caching
- Add provider health monitoring
- Rate limit tracking/warnings

### Metrics
- Additional financial ratios
- Historical trend analysis
- Peer comparison
- Sector averages

---

## Dependencies

### Backend
- fastapi
- uvicorn[standard]
- requests
- yfinance
- pandas
- python-dotenv
- pydantic-settings
- cryptography

### Frontend
- react
- @mui/material
- @emotion/react
- @emotion/styled
- vite

---

## Git Workflow

**Current Branch**: `fix_hardcoded_urls`

**Recent Work**:
- Removed hardcoded URLs across codebase
- Implemented custom exception system
- Updated all providers with consistent error handling
- Enhanced error messages with provider transparency

**Commit Pattern**:
```bash
git add .
git commit -m "descriptive message

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Additional Notes

### 12-Factor App Compliance
- All configuration via environment variables
- No hardcoded URLs or secrets in code
- Separate configs for dev/staging/production
- `.env` files for local development
- `.env.example` files for documentation

### Code Quality
- Type hints throughout Python code
- Comprehensive error handling
- Descriptive variable/function names
- Comments explaining non-obvious logic
- Separation of concerns (services, routers, models)

### Security Considerations
- OAuth tokens encrypted at rest
- HTTPS required for OAuth callback
- No secrets in version control
- Environment-based configuration
- HTTP Basic Auth for Schwab token exchange

---

## Contact & Resources

- **Schwab Developer Portal**: https://developer.schwab.com/
- **Alpha Vantage**: https://www.alphavantage.co/
- **Polygon.io**: https://polygon.io/
- **yfinance Documentation**: https://pypi.org/project/yfinance/

---

*Last Updated: 2025-12-11*

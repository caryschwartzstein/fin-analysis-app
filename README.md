# Financial Analysis Dashboard

A full-stack application for analyzing stock financial metrics and retrieving real-time market data through multiple providers including Schwab Developer API (OAuth 2.0), Yahoo Finance, Alpha Vantage, and Polygon.io.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![React](https://img.shields.io/badge/react-18+-blue.svg)

## Features

✨ **Real-Time Market Data**
- Schwab Developer API integration with OAuth 2.0
- Live stock quotes with price, volume, and fundamentals
- Multiple data provider support with automatic fallback

📊 **Financial Metrics**
- ROCE (Return on Capital Employed)
- Earnings Yield
- Enterprise Value
- Working Capital
- Historical financial statements

🔐 **Secure Authentication**
- OAuth 2.0 authorization flow
- Encrypted token storage (Fernet)
- Automatic token refresh
- HTTPS/SSL support

🎯 **Intelligent Error Handling**
- Provider-specific error detection
- Transparent error messages with provider context
- Automatic fallback to alternative providers
- Rate limit detection and guidance

## Quick Start

### Prerequisites

- Python 3.9+
- Node.js 16+
- npm or yarn

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd fin-analysis
```

2. **Backend Setup**
```bash
cd fin-analysis-api

# Install dependencies
pip install -r requirements.txt

# Generate SSL certificates for HTTPS
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Create .env file from template
cp .env.example .env

# Edit .env and add your API keys
nano .env
```

3. **Frontend Setup**
```bash
cd ../fin-analysis-app

# Install dependencies
npm install

# Create .env file from template (if needed)
cp .env.example .env
```

4. **Start the Application**

Backend:
```bash
cd fin-analysis-api
python main.py
```
Server runs at: `https://127.0.0.1:8000`

Frontend:
```bash
cd fin-analysis-app
npm run dev
```
App runs at: `http://localhost:5173`

5. **Accept SSL Certificate**
- Navigate to `https://127.0.0.1:8000` in your browser
- Accept the self-signed certificate warning
- Navigate to `http://localhost:5173` to use the app

## Configuration

### Required Environment Variables

**Backend** (`fin-analysis-api/.env`):
```bash
# Required
FRONTEND_URL=http://localhost:5173
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:5174,http://localhost:8000

# Optional but recommended
ALPHA_VANTAGE_API_KEY=your_api_key
```

**Schwab OAuth** (optional, for real-time quotes):
```bash
SCHWAB_APP_KEY=your_app_key
SCHWAB_APP_SECRET=your_app_secret
SCHWAB_REDIRECT_URI=https://127.0.0.1:8000/api/v1/oauth/callback
SCHWAB_ENCRYPTION_KEY=<generate_with_command_below>
```

Generate Fernet encryption key:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Usage

### Financial Metrics Analysis

1. Navigate to the Financial Metrics Analysis section
2. Enter a stock ticker (e.g., AAPL, MSFT, GOOGL)
3. Select timeframe (Annual or Quarterly)
4. Optionally select a specific data provider
5. Click "Get Metrics"

### Schwab Real-Time Quotes

1. Click "Connect to Schwab" in the header
2. Authenticate with your Schwab credentials
3. Grant API access permissions
4. After redirect, you'll see "Connected to Schwab"
5. Enter a stock symbol in the Schwab Quotes section
6. View real-time price, volume, and fundamentals

## API Endpoints

### Financial Metrics

**Get Stock Metrics**
```
GET /api/v1/metrics/{ticker}?timeframe=annual&provider=yfinance
```

**Get Financial Statements**
```
GET /api/v1/financials/{ticker}?timeframe=annual&limit=1
```

**Health Check**
```
GET /api/v1/health
```

### Schwab OAuth

**Initiate Connection**
```
GET /api/v1/oauth/connect
```

**Get Quote**
```
GET /api/v1/oauth/quote/{symbol}
```

**Check Status**
```
GET /api/v1/oauth/status
```

See `https://127.0.0.1:8000/docs` for interactive API documentation.

## Data Providers

### Yahoo Finance (yfinance)
- **Cost**: Free
- **Limitations**: Rate limiting may occur
- **Best for**: Quick testing, personal use

### Alpha Vantage
- **Cost**: Free (25 requests/day), paid tiers available
- **Setup**: Get free API key from [alphavantage.co](https://www.alphavantage.co/support/#api-key)
- **Limitations**: 25 API calls per day on free tier

### Polygon.io
- **Cost**: Paid subscription required
- **Setup**: Get API key from [polygon.io](https://polygon.io/)
- **Best for**: Production applications

### Schwab Developer API
- **Cost**: Free with approved application
- **Setup**: Register at [developer.schwab.com](https://developer.schwab.com/)
- **Requirements**: OAuth 2.0, HTTPS redirect URI

## Error Handling

The application provides transparent error messages with provider context:

**Rate Limit Errors (HTTP 429)**:
```
"Yahoo Finance rate limit exceeded. Please wait a few minutes and try again.
Consider using a different provider (alphavantage) if this persists. (Provider: yfinance)"
```

**Data Not Found (HTTP 404)**:
```
"No financial data available for ticker XYZ. The ticker may be invalid or
data is not available from Yahoo Finance. (Provider: yfinance)"
```

## Troubleshooting

### "Address already in use" Error
```bash
lsof -ti:8000 | xargs kill -9
```

### SSL Certificate Not Trusted
- This is expected with self-signed certificates
- Navigate to `https://127.0.0.1:8000` and accept the warning

### Yahoo Finance Rate Limiting
- Error: "Expecting value: line 1 column 1 (char 0)"
- Solution: Wait a few minutes or use `provider=alphavantage`

### Alpha Vantage "25 requests" Error
- Free tier limited to 25 requests per day
- Solution: Wait until next day or use `provider=yfinance`

## Documentation

For detailed documentation, see:
- [`claude.md`](./claude.md) - Comprehensive project documentation
- [`fin-analysis-api/README.md`](./fin-analysis-api/README.md) - Backend API details
- [`fin-analysis-app/README.md`](./fin-analysis-app/README.md) - Frontend details

## Tech Stack

**Backend:**
- FastAPI with HTTPS/SSL
- Python 3.9+
- yfinance, Alpha Vantage, Polygon.io, Schwab APIs
- Encrypted token storage (cryptography/Fernet)

**Frontend:**
- React 18
- Material-UI
- Vite
- Modern CSS

## License

This project is licensed under the MIT License.

## Resources

- [Schwab Developer Portal](https://developer.schwab.com/)
- [Alpha Vantage API](https://www.alphavantage.co/documentation/)
- [Polygon.io API](https://polygon.io/docs)
- [yfinance Documentation](https://pypi.org/project/yfinance/)

---

**Built with ❤️ using FastAPI and React**

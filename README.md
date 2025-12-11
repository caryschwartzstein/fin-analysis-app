# Financial Analysis Dashboard

A full-stack financial analysis application consisting of a FastAPI backend and React frontend.

## Project Structure

```
fin-analysis/
├── fin-analysis-api/     # FastAPI backend with financial data providers
└── fin-analysis-app/     # React frontend dashboard
```

## Quick Start

### Option 1: Using the start script (Linux/Mac)

```bash
./start-app.sh
```

This will start both the API server and React app simultaneously.

### Option 2: Manual start

#### 1. Start the API server

```bash
cd fin-analysis-api
source .venv/bin/activate  # or `.venv\Scripts\activate` on Windows
python main.py
```

The API will be available at http://localhost:8000

#### 2. Start the React app

In a new terminal:

```bash
cd fin-analysis-app
npm install  # first time only
npm run dev
```

The app will be available at http://localhost:5173

## Features

### Backend (fin-analysis-api)
- Multiple data providers: yfinance, Alpha Vantage, Polygon.io
- Financial metrics calculation (ROCE, Earnings Yield)
- RESTful API endpoints

### Frontend (fin-analysis-app)
- Interactive stock ticker search
- Timeframe selection (Annual/Quarterly)
- Provider selection
- Display of key financial metrics:
  - ROCE (Return on Capital Employed)
  - Earnings Yield
  - Market Cap
  - Stock Price
  - Shares Outstanding
  - Total Debt
  - Cash & Cash Equivalents
  - Total Assets
  - Current Liabilities

## API Endpoints

- `GET /api/v1/metrics/{ticker}?timeframe=annual&provider=yfinance`
- `GET /api/v1/financials/{ticker}?timeframe=annual&limit=1`
- `GET /api/v1/health`

See http://localhost:8000/docs for interactive API documentation.

## Usage Example

1. Open http://localhost:5173 in your browser
2. Enter a stock ticker (e.g., AAPL)
3. Select timeframe and provider
4. Click "Get Metrics"
5. View the financial analysis

## Tech Stack

**Backend:**
- FastAPI
- Python 3.9+
- yfinance, Alpha Vantage, Polygon.io APIs

**Frontend:**
- React 18
- Vite
- Modern CSS

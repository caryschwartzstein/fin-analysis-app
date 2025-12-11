# Financial Analysis App

A simple React app for viewing financial metrics from the fin-analysis-api.

## Features

- Input ticker symbol, timeframe (annual/quarterly), and data provider
- Display key financial metrics:
  - ROCE (Return on Capital Employed)
  - Earnings Yield
  - Market Cap
  - Stock Price
  - Shares Outstanding
  - Total Debt
  - Cash & Cash Equivalents
  - Total Assets
  - Current Liabilities

## Setup

1. Install dependencies:
```bash
npm install
```

2. Make sure the fin-analysis-api is running on `http://localhost:8000`

3. Start the development server:
```bash
npm run dev
```

4. Open your browser to `http://localhost:5173`

## Usage

1. Enter a stock ticker (e.g., AAPL, MSFT)
2. Select timeframe (Annual or Quarterly)
3. Optionally select a data provider (defaults to yfinance)
4. Click "Get Metrics" to view the financial data

## API Integration

This app connects to the fin-analysis-api at `http://localhost:8000/api/v1/metrics/{ticker}`.

Make sure CORS is properly configured in the API to allow requests from `http://localhost:5173`.

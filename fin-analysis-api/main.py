from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import financial_data, schwab_oauth

# Create FastAPI app
app = FastAPI(
    title="Financial Analysis API",
    description="Financial data API with hybrid provider support (yfinance, Alpha Vantage, Polygon.io) featuring ROCE and Earnings Yield calculations",
    version="3.0.0"
)

# Configure CORS (adjust origins as needed for your use case)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173", "http://localhost:5174", "http://localhost:8000"],  # Add your frontend origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(financial_data.router)
app.include_router(schwab_oauth.router)


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Financial Analysis API",
        "version": "3.0.0",
        "providers": {
            "supported": ["yfinance", "alphavantage", "polygon"],
            "default": "yfinance",
            "description": "Hybrid provider support with automatic fallback. Priority: yfinance (free, unlimited) > alphavantage (25/day) > polygon (deprecated endpoint)"
        },
        "endpoints": {
            "health": "/api/v1/health",
            "financials": "/api/v1/financials/{ticker}?timeframe=annual&limit=1",
            "metrics": "/api/v1/metrics/{ticker}?timeframe=annual",
            "docs": "/docs"
        },
        "examples": {
            "default": "/api/v1/metrics/AAPL?timeframe=annual",
            "alphavantage": "/api/v1/metrics/AAPL?timeframe=annual&provider=alphavantage",
            "yfinance": "/api/v1/metrics/AAPL?timeframe=annual&provider=yfinance"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        ssl_keyfile="key.pem",
        ssl_certfile="cert.pem"
    )
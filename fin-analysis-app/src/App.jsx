import { useState } from 'react';
import { getStockMetrics } from './services/api';
import MetricsDisplay from './components/MetricsDisplay';
import LoadingSpinner from './components/LoadingSpinner';
import './App.css';

function App() {
  const [ticker, setTicker] = useState('');
  const [timeframe, setTimeframe] = useState('annual');
  const [provider, setProvider] = useState('');
  const [metrics, setMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setMetrics(null);
    setLoading(true);

    try {
      const data = await getStockMetrics(
        ticker.toUpperCase(),
        timeframe,
        provider || null
      );
      setMetrics(data);
    } catch (err) {
      setError(err.message || 'Failed to fetch stock metrics');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>Financial Analysis Dashboard</h1>
      </header>

      <main className="app-main">
        <form className="input-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="ticker">Ticker Symbol</label>
            <input
              id="ticker"
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value)}
              placeholder="e.g., AAPL"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="timeframe">Timeframe</label>
            <select
              id="timeframe"
              value={timeframe}
              onChange={(e) => setTimeframe(e.target.value)}
            >
              <option value="annual">Annual</option>
              <option value="quarterly">Quarterly</option>
            </select>
          </div>

          <div className="form-group">
            <label htmlFor="provider">Provider (Optional)</label>
            <select
              id="provider"
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
            >
              <option value="">Default (yfinance)</option>
              <option value="yfinance">yfinance</option>
              <option value="alphavantage">Alpha Vantage</option>
              <option value="polygon">Polygon</option>
            </select>
          </div>

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading ? 'Loading...' : 'Get Metrics'}
          </button>
        </form>

        {loading && <LoadingSpinner />}

        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {metrics && !loading && <MetricsDisplay metrics={metrics} />}
      </main>
    </div>
  );
}

export default App;

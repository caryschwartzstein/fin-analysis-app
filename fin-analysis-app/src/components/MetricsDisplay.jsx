import InfoTooltip from './InfoTooltip';

const MetricsDisplay = ({ metrics }) => {
  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(num);
  };

  const formatLargeNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1e9) {
      return `$${(num / 1e9).toFixed(2)}B`;
    } else if (num >= 1e6) {
      return `$${(num / 1e6).toFixed(2)}M`;
    }
    return `$${formatNumber(num)}`;
  };

  const roceTooltip = (
    <div>
      <strong>ROCE Formula:</strong>
      <p>Operating Income ÷ Capital Employed</p>
      <br />
      <strong>Where:</strong>
      <p>Capital Employed = Total Assets - Current Liabilities</p>
      <br />
      <strong>Values:</strong>
      <p>Operating Income (EBIT): {formatLargeNumber(metrics.ebit)}</p>
      <p>Total Assets: {formatLargeNumber(metrics.total_assets)}</p>
      <p>Current Liabilities: {formatLargeNumber(metrics.current_liabilities)}</p>
      <p>Capital Employed: {formatLargeNumber(metrics.capital_employed)}</p>
    </div>
  );

  const earningsYieldTooltip = (
    <div>
      <strong>Earnings Yield Formula:</strong>
      <p>EBIT ÷ Enterprise Value</p>
      <br />
      <strong>Where:</strong>
      <p>Enterprise Value = Market Cap + Total Debt - Cash</p>
      <br />
      <strong>Values:</strong>
      <p>EBIT: {formatLargeNumber(metrics.ebit)}</p>
      <p>Market Cap: {formatLargeNumber(metrics.market_cap)}</p>
      <p>Total Debt: {formatLargeNumber(metrics.total_debt)}</p>
      <p>Cash & Equivalents: {formatLargeNumber(metrics.cash_and_equivalents)}</p>
      <p>Enterprise Value: {formatLargeNumber(metrics.enterprise_value)}</p>
    </div>
  );

  return (
    <div className="metrics-container">
      <h2>{metrics.ticker} - Financial Metrics</h2>
      <p className="date">As of: {metrics.date} ({metrics.period})</p>

      <div className="metrics-grid">
        <div className="metric-card primary">
          <div className="metric-header">
            <h3>ROCE</h3>
            <InfoTooltip content={roceTooltip} />
          </div>
          <p className="metric-value">{metrics.roce_percent || 'N/A'}</p>
        </div>

        <div className="metric-card primary">
          <div className="metric-header">
            <h3>Earnings Yield</h3>
            <InfoTooltip content={earningsYieldTooltip} />
          </div>
          <p className="metric-value">{metrics.earnings_yield_percent || 'N/A'}</p>
        </div>

        <div className="metric-card">
          <h3>Market Cap</h3>
          <p className="metric-value">{formatLargeNumber(metrics.market_cap)}</p>
        </div>

        <div className="metric-card">
          <h3>Stock Price</h3>
          <p className="metric-value">${formatNumber(metrics.stock_price)}</p>
        </div>

        <div className="metric-card">
          <h3>Shares Outstanding</h3>
          <p className="metric-value">{formatLargeNumber(metrics.shares_outstanding)}</p>
        </div>

        <div className="metric-card">
          <h3>Total Debt</h3>
          <p className="metric-value">{formatLargeNumber(metrics.total_debt)}</p>
        </div>

        <div className="metric-card">
          <h3>Cash & Equivalents</h3>
          <p className="metric-value">{formatLargeNumber(metrics.cash_and_equivalents)}</p>
        </div>

        <div className="metric-card">
          <h3>Total Assets</h3>
          <p className="metric-value">{formatLargeNumber(metrics.total_assets)}</p>
        </div>

        <div className="metric-card">
          <h3>Current Liabilities</h3>
          <p className="metric-value">{formatLargeNumber(metrics.current_liabilities)}</p>
        </div>
      </div>

      {metrics.notes && metrics.notes.length > 0 && (
        <div className="notes">
          <h4>Notes:</h4>
          <ul>
            {metrics.notes.map((note, idx) => (
              <li key={idx}>{note}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MetricsDisplay;

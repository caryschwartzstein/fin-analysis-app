import React, { useState } from 'react';
import { Card, CardContent, Typography, Box, Chip, CircularProgress, Button, TextField } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import TrendingDownIcon from '@mui/icons-material/TrendingDown';
import { useSnackbar } from './SnackbarProvider';
import { getSchwabQuote } from '../services/schwabApi';

const SchwabQuote = () => {
  const [symbol, setSymbol] = useState('');
  const [quote, setQuote] = useState(null);
  const [loading, setLoading] = useState(false);
  const { showSnackbar } = useSnackbar();

  const handleGetQuote = async (e) => {
    e.preventDefault();
    if (!symbol.trim()) return;

    setLoading(true);
    try {
      const data = await getSchwabQuote(symbol.toUpperCase());
      setQuote(data);
    } catch (error) {
      showSnackbar(error.message || 'Failed to get quote', 'error');
      setQuote(null);
    } finally {
      setLoading(false);
    }
  };

  const formatNumber = (num) => {
    if (!num) return 'N/A';
    return new Intl.NumberFormat('en-US').format(num);
  };

  const formatCurrency = (num) => {
    if (!num) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(num);
  };

  const formatPercent = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return `${num.toFixed(2)}%`;
  };

  // Extract quote data safely
  const getQuoteData = () => {
    if (!quote) return null;

    // The quote response has the symbol as the key
    const symbolKey = Object.keys(quote)[0];
    return quote[symbolKey];
  };

  const quoteData = getQuoteData();

  return (
    <Box sx={{ width: '100%' }}>
      <form onSubmit={handleGetQuote}>
        <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
          <TextField
            label="Stock Symbol"
            variant="outlined"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value.toUpperCase())}
            placeholder="e.g., AAPL"
            size="small"
            sx={{ flexGrow: 1 }}
          />
          <Button
            type="submit"
            variant="contained"
            disabled={loading || !symbol.trim()}
            sx={{ minWidth: '120px' }}
          >
            {loading ? <CircularProgress size={24} /> : 'Get Quote'}
          </Button>
        </Box>
      </form>

      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {quoteData && !loading && (
        <Card elevation={3}>
          <CardContent>
            {/* Header */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="h4" component="h2" sx={{ fontWeight: 'bold' }}>
                {quoteData.symbol}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {quoteData.reference?.description || 'N/A'}
              </Typography>
              <Typography variant="caption" color="text.secondary">
                {quoteData.reference?.exchangeName || 'N/A'}
              </Typography>
            </Box>

            {/* Price Section */}
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2 }}>
                <Typography variant="h3" component="div" sx={{ fontWeight: 'bold' }}>
                  {formatCurrency(quoteData.quote?.lastPrice)}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {quoteData.quote?.netChange >= 0 ? (
                    <TrendingUpIcon color="success" />
                  ) : (
                    <TrendingDownIcon color="error" />
                  )}
                  <Typography
                    variant="h6"
                    sx={{
                      color: quoteData.quote?.netChange >= 0 ? 'success.main' : 'error.main',
                      fontWeight: 'bold',
                    }}
                  >
                    {formatCurrency(quoteData.quote?.netChange)} (
                    {formatPercent(quoteData.quote?.netPercentChange)})
                  </Typography>
                </Box>
              </Box>
              <Chip
                label={quoteData.quote?.securityStatus || 'Unknown'}
                size="small"
                color={quoteData.quote?.securityStatus === 'Closed' ? 'default' : 'success'}
                sx={{ mt: 1 }}
              />
            </Box>

            {/* Key Stats Grid */}
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
                gap: 2,
                mb: 3,
              }}
            >
              <Box>
                <Typography variant="caption" color="text.secondary">
                  OPEN
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {formatCurrency(quoteData.quote?.openPrice)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  HIGH
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {formatCurrency(quoteData.quote?.highPrice)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  LOW
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {formatCurrency(quoteData.quote?.lowPrice)}
                </Typography>
              </Box>
              <Box>
                <Typography variant="caption" color="text.secondary">
                  VOLUME
                </Typography>
                <Typography variant="body1" fontWeight="medium">
                  {formatNumber(quoteData.quote?.totalVolume)}
                </Typography>
              </Box>
            </Box>

            {/* 52 Week Range */}
            <Box sx={{ mb: 3 }}>
              <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                52 WEEK RANGE
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <Typography variant="body2">
                  {formatCurrency(quoteData.quote?.['52WeekLow'])}
                </Typography>
                <Box
                  sx={{
                    flexGrow: 1,
                    height: 8,
                    bgcolor: 'grey.200',
                    borderRadius: 1,
                    position: 'relative',
                  }}
                >
                  <Box
                    sx={{
                      position: 'absolute',
                      left: `${
                        ((quoteData.quote?.lastPrice - quoteData.quote?.['52WeekLow']) /
                          (quoteData.quote?.['52WeekHigh'] - quoteData.quote?.['52WeekLow'])) *
                        100
                      }%`,
                      top: -4,
                      width: 16,
                      height: 16,
                      bgcolor: 'primary.main',
                      borderRadius: '50%',
                      border: '2px solid white',
                    }}
                  />
                </Box>
                <Typography variant="body2">
                  {formatCurrency(quoteData.quote?.['52WeekHigh'])}
                </Typography>
              </Box>
            </Box>

            {/* Fundamentals */}
            {quoteData.fundamental && (
              <Box
                sx={{
                  display: 'grid',
                  gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                  gap: 2,
                  pt: 2,
                  borderTop: '1px solid',
                  borderColor: 'divider',
                }}
              >
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    P/E RATIO
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {quoteData.fundamental.peRatio?.toFixed(2) || 'N/A'}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    DIV YIELD
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatPercent(quoteData.fundamental.divYield * 100)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    EPS
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatCurrency(quoteData.fundamental.eps)}
                  </Typography>
                </Box>
                <Box>
                  <Typography variant="caption" color="text.secondary">
                    AVG VOLUME (10D)
                  </Typography>
                  <Typography variant="body1" fontWeight="medium">
                    {formatNumber(quoteData.fundamental.avg10DaysVolume)}
                  </Typography>
                </Box>
              </Box>
            )}

            {/* Real-time indicator */}
            <Box sx={{ mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
              <Typography variant="caption" color="text.secondary">
                {quoteData.realtime ? '🟢 Real-time data' : '⏱️ Delayed data'} • Last updated:{' '}
                {new Date(quoteData.quote?.quoteTime).toLocaleTimeString()}
              </Typography>
            </Box>
          </CardContent>
        </Card>
      )}
    </Box>
  );
};

export default SchwabQuote;

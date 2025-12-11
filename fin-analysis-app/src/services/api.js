const API_BASE_URL = 'https://127.0.0.1:8000/api/v1';

export const getStockMetrics = async (ticker, timeframe = 'annual', provider = null) => {
  try {
    const params = new URLSearchParams({ timeframe });
    if (provider) {
      params.append('provider', provider);
    }

    const response = await fetch(`${API_BASE_URL}/metrics/${ticker}?${params}`);

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Failed to fetch stock metrics');
    }

    return await response.json();
  } catch (error) {
    throw error;
  }
};

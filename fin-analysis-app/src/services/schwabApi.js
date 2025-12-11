const API_BASE_URL = 'https://127.0.0.1:8000';

export const getSchwabAuthUrl = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/oauth/connect`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get authorization URL');
  }

  const data = await response.json();
  return data.auth_url;
};

export const getSchwabStatus = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/oauth/status`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to get Schwab status');
  }

  return response.json();
};

export const disconnectSchwab = async () => {
  const response = await fetch(`${API_BASE_URL}/api/v1/oauth/disconnect`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    throw new Error('Failed to disconnect from Schwab');
  }

  return response.json();
};

export const getSchwabQuote = async (symbol) => {
  const response = await fetch(`${API_BASE_URL}/api/v1/oauth/quote/${symbol}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to get quote');
  }

  return response.json();
};

import React, { useState, useEffect } from 'react';
import { Button, Chip, CircularProgress, Box } from '@mui/material';
import { useSnackbar } from './SnackbarProvider';
import { getSchwabAuthUrl, getSchwabStatus, disconnectSchwab } from '../services/schwabApi';

const SchwabConnect = () => {
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const { showSnackbar } = useSnackbar();

  // Check connection status on mount
  useEffect(() => {
    checkStatus();
  }, []);

  // Handle OAuth callback
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const schwabStatus = params.get('schwab');

    if (schwabStatus === 'connected') {
      showSnackbar('Connected to Schwab successfully!', 'success');
      // Remove query params from URL
      window.history.replaceState({}, document.title, window.location.pathname);
      // Refresh status
      checkStatus();
    } else if (schwabStatus === 'denied') {
      showSnackbar('Schwab connection was denied', 'error');
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (schwabStatus === 'error') {
      const errorMessage = params.get('message') || 'Unknown error';
      showSnackbar(`Connection failed: ${errorMessage.replace(/_/g, ' ')}`, 'error');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const statusData = await getSchwabStatus();
      setStatus(statusData);
    } catch (error) {
      console.error('Failed to check Schwab status:', error);
      setStatus({ connected: false });
    } finally {
      setLoading(false);
    }
  };

  const handleConnect = async () => {
    try {
      const authUrl = await getSchwabAuthUrl();
      // Redirect to Schwab authorization page
      window.location.href = authUrl;
    } catch (error) {
      showSnackbar('Failed to initiate Schwab connection', 'error');
    }
  };

  const handleDisconnect = async () => {
    try {
      await disconnectSchwab();
      showSnackbar('Disconnected from Schwab', 'info');
      await checkStatus();
    } catch (error) {
      showSnackbar('Failed to disconnect from Schwab', 'error');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={20} />
        <span>Checking Schwab connection...</span>
      </Box>
    );
  }

  return (
    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
      {status?.connected ? (
        <>
          <Chip
            label="Connected to Schwab"
            color="success"
            variant="outlined"
            size="small"
          />
          <Button
            variant="outlined"
            size="small"
            onClick={handleDisconnect}
          >
            Disconnect
          </Button>
        </>
      ) : (
        <Button
          variant="contained"
          color="primary"
          onClick={handleConnect}
        >
          Connect to Schwab
        </Button>
      )}
    </Box>
  );
};

export default SchwabConnect;

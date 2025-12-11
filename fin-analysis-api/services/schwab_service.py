"""
Schwab API Service
Handles OAuth authentication and API interactions with Schwab
"""
import os
import requests
from typing import Dict, Optional
from urllib.parse import urlencode
from services.token_manager import TokenManager


class SchwabService:
    """Service for interacting with Schwab API"""

    # Schwab OAuth endpoints
    AUTHORIZATION_URL = "https://api.schwabapi.com/v1/oauth/authorize"
    TOKEN_URL = "https://api.schwabapi.com/v1/oauth/token"

    # Schwab API base URL
    API_BASE_URL = "https://api.schwabapi.com"

    def __init__(self, app_key: str, app_secret: str, redirect_uri: str, token_manager: TokenManager):
        """
        Initialize Schwab service

        Args:
            app_key: Schwab App Key
            app_secret: Schwab App Secret
            redirect_uri: OAuth redirect URI
            token_manager: TokenManager instance for token storage
        """
        self.app_key = app_key
        self.app_secret = app_secret
        self.redirect_uri = redirect_uri
        self.token_manager = token_manager

    def get_authorization_url(self) -> str:
        """
        Generate the authorization URL for OAuth flow

        Returns:
            Full authorization URL for user to visit
        """
        params = {
            "client_id": self.app_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code"
        }

        return f"{self.AUTHORIZATION_URL}?{urlencode(params)}"

    def exchange_code_for_tokens(self, authorization_code: str) -> Dict:
        """
        Exchange authorization code for access and refresh tokens

        Args:
            authorization_code: The authorization code from callback

        Returns:
            Dictionary containing tokens

        Raises:
            Exception: If token exchange fails
        """
        data = {
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Schwab requires HTTP Basic Authentication
        response = requests.post(
            self.TOKEN_URL,
            data=data,
            headers=headers,
            auth=(self.app_key, self.app_secret)
        )

        if response.status_code != 200:
            raise Exception(f"Token exchange failed: {response.status_code} - {response.text}")

        tokens = response.json()

        # Save tokens using token manager
        self.token_manager.save_tokens(tokens)

        return tokens

    def refresh_access_token(self) -> Dict:
        """
        Refresh the access token using the refresh token

        Returns:
            Dictionary containing new tokens

        Raises:
            Exception: If refresh fails
        """
        tokens = self.token_manager.get_tokens()

        if not tokens or 'refresh_token' not in tokens:
            raise Exception("No refresh token available")

        data = {
            "grant_type": "refresh_token",
            "refresh_token": tokens['refresh_token']
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        # Schwab requires HTTP Basic Authentication
        response = requests.post(
            self.TOKEN_URL,
            data=data,
            headers=headers,
            auth=(self.app_key, self.app_secret)
        )

        if response.status_code != 200:
            raise Exception(f"Token refresh failed: {response.status_code} - {response.text}")

        new_tokens = response.json()

        # Save new tokens
        self.token_manager.save_tokens(new_tokens)

        return new_tokens

    def get_valid_access_token(self) -> str:
        """
        Get a valid access token, refreshing if necessary (proactive refresh)

        Returns:
            Valid access token

        Raises:
            Exception: If no tokens exist or refresh fails
        """
        # Check if access token is expired or will expire soon
        if self.token_manager.is_access_token_expired():
            # If refresh token is valid, refresh
            if self.token_manager.is_refresh_token_valid():
                tokens = self.refresh_access_token()
                return tokens['access_token']
            else:
                raise Exception("No valid tokens available. User needs to re-authenticate.")

        # Access token is still valid
        tokens = self.token_manager.get_tokens()
        return tokens['access_token']

    def get_quote(self, symbol: str) -> Dict:
        """
        Get real-time quote for a symbol

        Args:
            symbol: Stock symbol (e.g., 'AAPL')

        Returns:
            Quote data

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_valid_access_token()

        # Schwab uses /marketdata/v1/{symbol}/quotes endpoint
        url = f"{self.API_BASE_URL}/marketdata/v1/{symbol}/quotes"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            raise Exception(f"Failed to get quote: {response.status_code} - {response.text}")

        return response.json()

    def get_quotes(self, symbols: list) -> Dict:
        """
        Get real-time quotes for multiple symbols

        Args:
            symbols: List of stock symbols (e.g., ['AAPL', 'GOOGL'])

        Returns:
            Quotes data for all symbols

        Raises:
            Exception: If API call fails
        """
        access_token = self.get_valid_access_token()

        # Join symbols with commas
        symbols_param = ",".join(symbols)
        url = f"{self.API_BASE_URL}/marketdata/v1/quotes"

        headers = {
            "Authorization": f"Bearer {access_token}"
        }

        params = {
            "symbols": symbols_param
        }

        response = requests.get(url, headers=headers, params=params)

        if response.status_code != 200:
            raise Exception(f"Failed to get quotes: {response.status_code} - {response.text}")

        return response.json()

    def revoke_tokens(self) -> bool:
        """
        Revoke tokens and delete from storage

        Returns:
            True if successful
        """
        # Note: Schwab may or may not have a revocation endpoint
        # For now, we just delete local tokens
        return self.token_manager.delete_tokens()

"""
Schwab OAuth Router
Handles OAuth authentication flow endpoints
"""
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from services.schwab_service import SchwabService
from services.token_manager import TokenManager
from config import settings


# Initialize router
# TODO: Rename router prefix from "/api/v1/oauth" to "/api/v1/schwab" after updating
# redirect URI in Schwab Developer Portal. Current prefix matches registered callback.
# Schwab has a waiting period before redirect URI changes take effect.
router = APIRouter(prefix="/api/v1/oauth", tags=["schwab"])

# Initialize token manager and Schwab service
token_manager = TokenManager(
    encryption_key=settings.schwab_encryption_key,
    storage_path="tokens/schwab_tokens.enc"
)

schwab_service = SchwabService(
    app_key=settings.schwab_app_key,
    app_secret=settings.schwab_app_secret,
    redirect_uri=settings.schwab_redirect_uri,
    token_manager=token_manager
)


class ConnectionStatus(BaseModel):
    """Model for connection status response"""
    connected: bool
    expires_at: Optional[str] = None
    needs_refresh: bool = False
    message: str


class AuthorizationURL(BaseModel):
    """Model for authorization URL response"""
    auth_url: str


class QuoteRequest(BaseModel):
    """Model for quote request"""
    symbol: str


@router.get("/connect", response_model=AuthorizationURL)
async def connect():
    """
    Initiate OAuth flow by returning authorization URL

    Returns:
        Authorization URL for user to visit
    """
    try:
        auth_url = schwab_service.get_authorization_url()
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate authorization URL: {str(e)}")


@router.get("/callback")
async def oauth_callback(
    code: Optional[str] = Query(None),
    error: Optional[str] = Query(None)
):
    """
    OAuth callback endpoint - receives authorization code from Schwab

    Args:
        code: Authorization code from Schwab
        error: Error message if user denied access

    Returns:
        Redirect to frontend with success/error status
    """
    # Handle user denial
    if error:
        return RedirectResponse(url=f"{settings.frontend_url}/?schwab=denied&error={error}")

    # Validate code exists
    if not code:
        return RedirectResponse(url=f"{settings.frontend_url}/?schwab=error&message=no_code")

    try:
        # Exchange code for tokens
        tokens = schwab_service.exchange_code_for_tokens(code)

        # Redirect to frontend with success
        return RedirectResponse(url=f"{settings.frontend_url}/?schwab=connected")

    except Exception as e:
        # Redirect to frontend with error
        error_message = str(e).replace(" ", "_")
        return RedirectResponse(url=f"{settings.frontend_url}/?schwab=error&message={error_message}")


@router.get("/status", response_model=ConnectionStatus)
async def get_status():
    """
    Check Schwab connection status

    Returns:
        Connection status including token expiration info
    """
    try:
        tokens = token_manager.get_tokens()

        if not tokens:
            return {
                "connected": False,
                "expires_at": None,
                "needs_refresh": False,
                "message": "Not connected to Schwab"
            }

        # Check if tokens are valid
        is_expired = token_manager.is_access_token_expired()
        has_refresh = token_manager.is_refresh_token_valid()

        if is_expired and not has_refresh:
            return {
                "connected": False,
                "expires_at": tokens.get('expires_at'),
                "needs_refresh": False,
                "message": "Session expired - please reconnect"
            }

        return {
            "connected": True,
            "expires_at": tokens.get('expires_at'),
            "needs_refresh": is_expired,
            "message": "Connected to Schwab" if not is_expired else "Token will be refreshed automatically"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check status: {str(e)}")


@router.post("/disconnect")
async def disconnect():
    """
    Disconnect from Schwab by revoking and deleting tokens

    Returns:
        Success message
    """
    try:
        success = schwab_service.revoke_tokens()

        if success:
            return {"message": "Disconnected from Schwab successfully"}
        else:
            return {"message": "No active connection to disconnect"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@router.post("/refresh")
async def refresh_token():
    """
    Manually trigger token refresh (optional - tokens auto-refresh when needed)

    Returns:
        Success message
    """
    try:
        tokens = schwab_service.refresh_access_token()
        return {
            "message": "Tokens refreshed successfully",
            "expires_at": tokens.get('expires_at')
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Failed to refresh token: {str(e)}")


@router.get("/quote/{symbol}")
async def get_quote(symbol: str):
    """
    Get real-time quote for a symbol (example API endpoint)

    Args:
        symbol: Stock symbol (e.g., 'AAPL')

    Returns:
        Quote data from Schwab
    """
    try:
        quote = schwab_service.get_quote(symbol.upper())
        return quote
    except Exception as e:
        if "No valid tokens" in str(e):
            raise HTTPException(status_code=401, detail="Not authenticated. Please connect to Schwab first.")
        raise HTTPException(status_code=500, detail=f"Failed to get quote: {str(e)}")


@router.get("/quotes")
async def get_quotes(symbols: str = Query(..., description="Comma-separated stock symbols")):
    """
    Get real-time quotes for multiple symbols

    Args:
        symbols: Comma-separated stock symbols (e.g., 'AAPL,GOOGL,MSFT')

    Returns:
        Quotes data from Schwab
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(",")]
        quotes = schwab_service.get_quotes(symbol_list)
        return quotes
    except Exception as e:
        if "No valid tokens" in str(e):
            raise HTTPException(status_code=401, detail="Not authenticated. Please connect to Schwab first.")
        raise HTTPException(status_code=500, detail=f"Failed to get quotes: {str(e)}")

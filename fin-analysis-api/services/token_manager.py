"""
Token Manager Service
Handles encrypted storage and retrieval of Schwab OAuth tokens
"""
import os
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from cryptography.fernet import Fernet
from pathlib import Path


class TokenManager:
    """Manages encrypted storage of OAuth tokens"""

    def __init__(self, encryption_key: str, storage_path: str = "tokens/schwab_tokens.enc"):
        """
        Initialize token manager

        Args:
            encryption_key: Base64-encoded Fernet encryption key
            storage_path: Path to encrypted token storage file
        """
        self.cipher = Fernet(encryption_key.encode())
        self.storage_path = Path(storage_path)

        # Ensure tokens directory exists
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def save_tokens(self, tokens: Dict) -> None:
        """
        Encrypt and save tokens to file

        Args:
            tokens: Dictionary containing access_token, refresh_token, expires_in, etc.
        """
        # Add timestamp for when tokens were saved
        tokens['saved_at'] = datetime.now().isoformat()

        # Calculate expiration timestamp if expires_in is provided
        if 'expires_in' in tokens:
            expires_at = datetime.now() + timedelta(seconds=tokens['expires_in'])
            tokens['expires_at'] = expires_at.isoformat()

        # Serialize to JSON
        json_data = json.dumps(tokens, indent=2)

        # Encrypt
        encrypted_data = self.cipher.encrypt(json_data.encode())

        # Write to file
        self.storage_path.write_bytes(encrypted_data)

    def get_tokens(self) -> Optional[Dict]:
        """
        Load and decrypt tokens from file

        Returns:
            Dictionary containing tokens, or None if no tokens exist
        """
        if not self.storage_path.exists():
            return None

        try:
            # Read encrypted data
            encrypted_data = self.storage_path.read_bytes()

            # Decrypt
            decrypted_data = self.cipher.decrypt(encrypted_data)

            # Parse JSON
            tokens = json.loads(decrypted_data.decode())

            return tokens
        except Exception as e:
            print(f"Error reading tokens: {e}")
            return None

    def delete_tokens(self) -> bool:
        """
        Delete stored tokens

        Returns:
            True if tokens were deleted, False if they didn't exist
        """
        if self.storage_path.exists():
            self.storage_path.unlink()
            return True
        return False

    def is_access_token_expired(self) -> bool:
        """
        Check if the access token is expired or will expire soon

        Returns:
            True if token is expired or will expire in < 5 minutes
        """
        tokens = self.get_tokens()
        if not tokens or 'expires_at' not in tokens:
            return True

        expires_at = datetime.fromisoformat(tokens['expires_at'])
        buffer_time = timedelta(minutes=5)

        return datetime.now() >= (expires_at - buffer_time)

    def is_refresh_token_valid(self) -> bool:
        """
        Check if we have a refresh token

        Returns:
            True if refresh token exists
        """
        tokens = self.get_tokens()
        return tokens is not None and 'refresh_token' in tokens and tokens['refresh_token']

    def has_valid_tokens(self) -> bool:
        """
        Check if we have valid tokens (either valid access token or valid refresh token)

        Returns:
            True if we have usable tokens
        """
        tokens = self.get_tokens()
        if not tokens:
            return False

        # If access token is still valid, we're good
        if not self.is_access_token_expired():
            return True

        # If access token expired but we have refresh token, we can refresh
        return self.is_refresh_token_valid()

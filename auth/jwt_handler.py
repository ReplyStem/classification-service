"""
JWT Authentication Handler.

Handles JWT token verification for incoming events.
"""

import jwt
from typing import Dict, Any, Optional
from datetime import datetime

from config.settings import get_settings


class JWTError(Exception):
    """Custom exception for JWT-related errors."""
    pass


class JWTHandler:
    """
    Handles JWT token verification.
    
    Usage:
        handler = JWTHandler()
        payload = handler.verify_token(token)
    """
    
    def __init__(self):
        """Initialize with settings."""
        self._settings = get_settings()
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify a JWT token and return its payload.
        
        Args:
            token: The JWT token string (without 'Bearer ' prefix)
            
        Returns:
            The decoded token payload
            
        Raises:
            JWTError: If token is invalid, expired, or malformed
        """
        try:
            payload = jwt.decode(
                token,
                self._settings.JWT_SECRET,
                algorithms=[self._settings.JWT_ALGORITHM]
            )
            return payload
        except jwt.ExpiredSignatureError:
            raise JWTError("Token has expired")
        except jwt.InvalidTokenError as e:
            raise JWTError(f"Invalid token: {str(e)}")
    
    @staticmethod
    def encode_token(
        payload: Dict[str, Any],
        secret: str,
        algorithm: str = "HS256"
    ) -> str:
        """
        Encode a payload into a JWT token.
        
        This is a utility method for testing/demo purposes.
        In production, tokens would be issued by an auth service.
        
        Args:
            payload: Data to encode in the token
            secret: Secret key for signing
            algorithm: Signing algorithm (default: HS256)
            
        Returns:
            Encoded JWT token string
        """
        return jwt.encode(payload, secret, algorithm=algorithm)


# ─────────────────────────────────────────────────────────────────────────────
# Example: How to generate a test token
# ─────────────────────────────────────────────────────────────────────────────
# 
# Run this in Python to generate a test token:
#
# ```python
# import jwt
# from datetime import datetime, timedelta
#
# secret = "your-super-secret-key-here"  # Same as JWT_SECRET in .env
# payload = {
#     "sub": "tenant_123",
#     "tenant_id": "tenant_123",
#     "iat": datetime.utcnow(),
#     "exp": datetime.utcnow() + timedelta(hours=24)
# }
# token = jwt.encode(payload, secret, algorithm="HS256")
# print(f"Bearer {token}")
# ```
# ─────────────────────────────────────────────────────────────────────────────

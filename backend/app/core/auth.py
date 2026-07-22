from typing import Optional
from fastapi import Request
from fastapi.security import OAuth2PasswordBearer
from config import settings

# OAuth2 scheme configured with token URL
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login",
    auto_error=False
)

def extract_token_from_header(request: Request) -> Optional[str]:
    """
    Extract Authorization Bearer token from Request headers.
    Supports case-insensitive header lookup and handles extra 'Bearer' prefixes.
    """
    auth_header = request.headers.get("Authorization") or request.headers.get("authorization")
    if not auth_header:
        return None
    
    parts = auth_header.strip().split()
    if not parts:
        return None
    
    # Extract token part safely
    token = parts[-1].strip()
    return token


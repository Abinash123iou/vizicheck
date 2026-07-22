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
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    return auth_header.split(" ", 1)[1].strip()

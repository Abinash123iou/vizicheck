from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from jose import JWTError, ExpiredSignatureError, jwt
from config import settings
from app.core.exceptions import ExpiredTokenException, InvalidTokenException

def create_access_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT access token.
    Payload contains: sub, email, role, tenant_id, permissions, token_type, iat, exp.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "token_type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })

    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def create_refresh_token(
    data: Dict[str, Any], 
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a signed JWT refresh token.
    Payload contains: sub, email, role, tenant_id, token_type, iat, exp.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)

    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "token_type": "refresh",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp())
    })

    encoded_jwt = jwt.encode(
        to_encode, 
        settings.JWT_SECRET, 
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT token.
    Raises ExpiredTokenException if expired, InvalidTokenException if signature/structure is invalid.
    """
    try:
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET, 
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        raise ExpiredTokenException("Authentication token has expired")
    except JWTError:
        raise InvalidTokenException("Invalid or malformed authentication token")

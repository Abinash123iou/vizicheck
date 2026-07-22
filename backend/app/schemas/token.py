from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field

class TokenResponseData(BaseModel):
    """
    Data payload for token refresh endpoint.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(..., description="Access token lifespan in seconds")

class TokenPayload(BaseModel):
    """
    Validated structure of claims extracted from JWT tokens.
    Never stores sensitive information.
    """
    sub: str
    email: EmailStr
    role: str
    tenant_id: Optional[int] = None
    permissions: List[str] = Field(default_factory=list)
    token_type: str
    iat: int
    exp: int

    model_config = ConfigDict(from_attributes=True)

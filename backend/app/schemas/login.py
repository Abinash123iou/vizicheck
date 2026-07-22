from pydantic import BaseModel, EmailStr, Field
from app.schemas.auth import UserProfileResponse

class LoginRequest(BaseModel):
    """
    Login credentials payload.
    """
    email: EmailStr = Field(..., description="User account email address")
    password: str = Field(..., min_length=1, description="Account password")

class LoginResponseData(BaseModel):
    """
    Data payload returned upon successful login.
    """
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserProfileResponse

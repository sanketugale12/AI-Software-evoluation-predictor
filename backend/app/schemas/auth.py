from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class AuthUrlResponse(BaseModel):
    url: str
    state: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: Optional[int] = None
    scope: Optional[str] = None


class UserResponse(BaseModel):
    id: str
    github_id: str
    username: str
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AuthStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[UserResponse] = None


class LogoutResponse(BaseModel):
    success: bool
    message: str
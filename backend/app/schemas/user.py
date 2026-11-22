from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

class UserRole(str, Enum):
    MEMBER = "MEMBER"
    AGENT = "AGENT"
    SUPPORT_HEAD = "SUPPORT_HEAD"

class UserBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: str = Field(..., min_length=3, max_length=255)
    role: UserRole

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class UserOut(UserBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=255)
    password: str

class MockLoginRequest(BaseModel):
    role: UserRole
    email: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut

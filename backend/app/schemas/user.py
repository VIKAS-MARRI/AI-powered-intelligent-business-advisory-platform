"""
Pydantic schemas for authentication and user responses.
"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


# ---------------------------------------------------------------------------
# Auth — Request / Response schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Minimum 8 characters")
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: str = "en"

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


# ---------------------------------------------------------------------------
# User schemas
# ---------------------------------------------------------------------------

class UserPublic(BaseModel):
    """Safe user data returned to the client — never includes hashed_password."""
    id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    preferred_language: str
    state: Optional[str]
    district: Optional[str]
    village_town: Optional[str]
    available_capital: Optional[float]
    skills: Optional[str]
    experience_years: Optional[int]
    business_interests: Optional[str]
    monthly_income_goal: Optional[float]
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateProfileRequest(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    preferred_language: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    village_town: Optional[str] = None
    available_capital: Optional[float] = Field(None, ge=0)
    skills: Optional[str] = None
    experience_years: Optional[int] = Field(None, ge=0)
    business_interests: Optional[str] = None
    monthly_income_goal: Optional[float] = Field(None, ge=0)

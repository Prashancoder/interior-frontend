"""
User & Authentication Schemas for Decore AI
===========================================
Defines models for Customers, Sellers, and JWT Authentication.
"""

from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

class UserRole(str, Enum):
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"

class UserRegisterRequest(BaseModel):
    """Payload for user / seller registration."""
    name: str = Field(..., min_length=2, max_length=100, description="Full Name or Business Contact")
    email: str = Field(..., min_length=5, max_length=150, description="Unique Email Address")
    password: str = Field(..., min_length=6, description="Account Password (min 6 characters)")
    role: UserRole = Field(default=UserRole.CUSTOMER, description="Role: 'customer' or 'seller'")
    business_name: Optional[str] = Field(None, max_length=150, description="Optional Store / Business name for sellers")
    phone: Optional[str] = Field(None, max_length=20, description="Optional Phone Number")

class UserLoginRequest(BaseModel):
    """Payload for user / seller login."""
    email: str = Field(..., description="Registered Email Address")
    password: str = Field(..., description="Account Password")

class UserResponse(BaseModel):
    """Public user profile response."""
    user_id: str = Field(..., description="Unique User Identifier")
    name: str
    email: str
    role: UserRole
    business_name: Optional[str] = None
    phone: Optional[str] = None
    is_active: bool = True
    created_at: Optional[str] = None

class TokenResponse(BaseModel):
    """JWT Token authentication response."""
    access_token: str = Field(..., description="Bearer JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse = Field(..., description="Authenticated user profile")

import hashlib
import json
import secrets
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, EmailStr, validator
from sqlmodel import Field, Relationship, SQLModel
from src.models.database import UserRole

# User Management Schemas
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    full_name: str
    password: str
    user_role: UserRole = UserRole.USER  # Default to USER role

    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username must be alphanumeric (with _ or - allowed)')
        return v

    @validator('password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    full_name: str
    user_role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    user_role: Optional[UserRole] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    username: str
    password: str

class UserChangePassword(BaseModel):
    current_password: str
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class AdminPasswordReset(BaseModel):
    new_password: str

    @validator('new_password')
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        return v

class TokenResponse(BaseModel):
    session_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
    
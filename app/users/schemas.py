"""Pydantic schemas for user endpoints."""

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    email: EmailStr
    password: str = Field(min_length=8)
    role: str = "user"


class UserRead(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileRead(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    department: str | None = None


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    bio: str | None = None
    department: str | None = None


class UserWithProfile(BaseModel):
    user: UserRead
    profile: UserProfileRead | None = None

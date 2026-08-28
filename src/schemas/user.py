from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from src.models.user import UserRole


class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=120)


class UserCreate(UserBase):
    password: str = Field(min_length=6, max_length=128)
    role: UserRole = UserRole.STUDENT


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: UserRole
    is_active: bool
    created_at: datetime


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

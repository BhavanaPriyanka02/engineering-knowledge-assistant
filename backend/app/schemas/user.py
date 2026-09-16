from datetime import datetime
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=128)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {
        "from_attributes": True,
    }

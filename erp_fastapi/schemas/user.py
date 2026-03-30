from pydantic import BaseModel, Field
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    email: str = Field(..., min_length=3, max_length=200)
    password: str = Field(..., min_length=6)
    role_id: Optional[int] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role_id: Optional[int] = None
    is_active: Optional[bool] = None


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    role_id: Optional[int] = None
    role_name: Optional[str] = None

    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserOut"


class LoginRequest(BaseModel):
    email: str
    password: str

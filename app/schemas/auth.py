"""
Схемы для аутентификации
"""
from pydantic import BaseModel, EmailStr, Field


class UserSignup(BaseModel):
    """Схема регистрации"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str
    role: str  # government, university, grantee


class UserLogin(BaseModel):
    """Схема входа"""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Схема ответа с пользователем"""
    id: int
    email: str
    name: str
    role: str
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """Схема токена"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

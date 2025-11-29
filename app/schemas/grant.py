"""
Схемы для грантов
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional


class GrantCreate(BaseModel):
    """Схема создания гранта"""
    title: str
    total_amount: Decimal
    university_id: int
    description: Optional[str] = None
    currency: Optional[str] = "USD"
    
    class Config:
        extra = "ignore"  # Игнорировать лишние поля


class GrantResponse(BaseModel):
    """Схема ответа с грантом"""
    id: int
    title: str
    total_amount: Decimal
    amount_spent: Decimal
    university_id: int
    state: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class GrantDetailResponse(GrantResponse):
    """Детальная схема гранта"""
    remaining_amount: Decimal


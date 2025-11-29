"""
Схемы для грантов
"""
from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal
from datetime import datetime


class GrantBase(BaseModel):
    """Базовая схема гранта"""
    title: str = Field(..., description="Название гранта")
    amount_total: Decimal = Field(..., description="Общая сумма гранта")
    grantee_id: int = Field(..., description="ID получателя гранта")
    blockchain_address: Optional[str] = Field(None, description="Адрес смарт-контракта")


class GrantCreate(GrantBase):
    """Схема для создания гранта"""
    pass


class GrantResponse(GrantBase):
    """Схема ответа с грантом"""
    id: int
    amount_spent: Decimal
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class GrantReport(BaseModel):
    """Схема отчёта по гранту"""
    grant_id: int
    title: str
    total_budget: Decimal
    spent: Decimal
    remaining: Decimal
    categories_breakdown: dict[str, Decimal]
    suspicious_expenses_count: int
    approved_expenses_count: int
    rejected_expenses_count: int
    pending_expenses_count: int
    funded_percentage: float
    rejected_percentage: float
    blockchain_hash: Optional[str] = None


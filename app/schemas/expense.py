"""
Схемы для расходов
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from app.models.expense import ExpenseStatus


class ExpenseBase(BaseModel):
    """Базовая схема расхода"""
    grant_id: int = Field(..., description="ID гранта")
    amount: Decimal = Field(..., description="Сумма расхода")
    category: Optional[str] = Field(None, description="Категория расхода")


class ExpenseCreate(ExpenseBase):
    """Схема для создания расхода"""
    description: Optional[str] = Field(None, description="Описание расхода")


class ExpenseManualCreate(BaseModel):
    """Схема для ручного создания расхода"""
    grant_id: int
    amount: Decimal
    description: Optional[str] = None
    category: Optional[str] = None


class ExpenseResponse(ExpenseBase):
    """Схема ответа с расходом"""
    id: int
    transaction_id: Optional[int] = None
    status: ExpenseStatus
    aml_flags: List[str]
    comment: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class ExpenseUpdate(BaseModel):
    """Схема для обновления расхода"""
    status: Optional[ExpenseStatus] = None
    comment: Optional[str] = None


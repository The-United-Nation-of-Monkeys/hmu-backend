"""
Схемы для расходов
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List


class SpendingItemCreate(BaseModel):
    """Схема создания мета-пункта"""
    grant_id: int
    title: str
    planned_amount: Decimal
    priority_index: int


class SpendingItemResponse(BaseModel):
    """Схема ответа с мета-пунктом"""
    id: int
    grant_id: int
    title: str
    planned_amount: Decimal
    priority_index: int
    
    class Config:
        from_attributes = True


class SpendingRequestCreate(BaseModel):
    """Схема создания запроса на транш"""
    grant_id: int
    spending_item_id: int
    amount: Decimal = Field(..., gt=0)


class SpendingRequestResponse(BaseModel):
    """Схема ответа с запросом на транш"""
    id: int
    spending_item_id: int
    grantee_id: int
    amount: Decimal
    status: str
    aml_flags: List[str]
    approved_by_university: Optional[int] = None
    paid_tx_hash: Optional[str] = None
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class SpendingRequestApprove(BaseModel):
    """Схема одобрения запроса"""
    approved: bool = True
    rejection_reason: Optional[str] = None


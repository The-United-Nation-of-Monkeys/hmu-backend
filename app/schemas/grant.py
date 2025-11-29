"""
Схемы для грантов
"""
from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional, List


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
    grantee_id: Optional[int] = None
    state: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class GrantDetailResponse(GrantResponse):
    """Детальная схема гранта"""
    remaining_amount: Decimal


class GrantAssignRequest(BaseModel):
    """Схема для назначения грантополучателя"""
    grantee_id: int


class GrantDetailForGranteeResponse(BaseModel):
    """Детальная схема гранта для грантополучателя с вложенными данными"""
    id: int
    title: str
    total_amount: Decimal
    amount_spent: Decimal
    university_id: int
    grantee_id: Optional[int] = None
    state: str
    created_at: datetime
    spending_items: List[dict]
    spending_requests: List[dict]
    
    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str
        }


class GrantDetailWithItemsResponse(GrantDetailResponse):
    """Детальная схема гранта с spending items и requests"""
    spending_items: List[dict]
    spending_requests: List[dict]


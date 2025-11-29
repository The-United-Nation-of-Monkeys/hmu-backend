"""
Схемы для транзакций
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from decimal import Decimal
from datetime import datetime


class MirWebhookRequest(BaseModel):
    """Схема webhook запроса от МИР"""
    transaction_id: str = Field(..., alias="transaction_id", description="ID транзакции от МИР")
    amount: Decimal = Field(..., description="Сумма транзакции")
    mcc: Optional[str] = Field(None, alias="mcc", description="Merchant Category Code")
    merchant: Optional[str] = Field(None, description="Название продавца")
    receipt: Optional[Dict[str, Any]] = Field(None, description="Данные чека")
    
    class Config:
        populate_by_name = True


class TransactionResponse(BaseModel):
    """Схема ответа с транзакцией"""
    id: int
    mir_id: str
    amount: Decimal
    mcc_code: Optional[str] = None
    merchant_name: Optional[str] = None
    has_receipt: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


"""
Схемы для AML
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from decimal import Decimal


class AMLCheckRequest(BaseModel):
    """Схема запроса на AML проверку"""
    transaction_id: Optional[int] = None
    expense_id: Optional[int] = None
    amount: Decimal
    merchant_name: Optional[str] = None
    grant_id: int
    grantee_name: Optional[str] = None


class AMLCheckResponse(BaseModel):
    """Схема ответа AML проверки"""
    flags: List[str] = Field(default_factory=list, description="Список флагов AML")
    is_suspicious: bool = Field(..., description="Подозрительная транзакция")
    recommendation: str = Field(..., description="Рекомендация (approve/review/reject)")


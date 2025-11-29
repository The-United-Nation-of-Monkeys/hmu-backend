"""
Роутер для AML (Anti-Money Laundering) проверок
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.models.user import User
from app.utils.enums import UserRole
from app.models.spending_request import SpendingRequest
from app.models.spending_item import SpendingItem
from sqlalchemy import select
from typing import List
from pydantic import BaseModel

router = APIRouter(prefix="/aml", tags=["AML"])


class AmlFlagResponse(BaseModel):
    """Схема ответа с AML флагом"""
    flag: str
    description: str
    severity: str  # low, medium, high


@router.get("/flags/{spending_request_id}", response_model=List[AmlFlagResponse])
async def get_flags(
    spending_request_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение AML флагов для запроса на транш"""
    result = await db.execute(
        select(SpendingRequest).where(SpendingRequest.id == spending_request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending request not found")
    
    flags = []
    if request.aml_flags:
        flag_descriptions = {
            "large_amount": "Сумма превышает 20% от размера гранта",
            "no_receipt": "Отсутствует чек",
            "suspicious_merchant": "Подозрительный продавец",
            "duplicated_transactions": "Дублирующиеся транзакции",
            "budget_exceeded": "Превышение бюджета",
            "affiliated_person": "Аффилированное лицо"
        }
        
        for flag in request.aml_flags:
            severity = "high" if flag in ["large_amount", "budget_exceeded"] else "medium"
            flags.append(AmlFlagResponse(
                flag=flag,
                description=flag_descriptions.get(flag, "Неизвестный флаг"),
                severity=severity
            ))
    
    return flags


@router.get("/flags/grant/{grant_id}", response_model=List[dict])
async def get_flags_by_grant(
    grant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение AML флагов по гранту"""
    # Получаем все spending items для гранта
    result = await db.execute(
        select(SpendingItem).where(SpendingItem.grant_id == grant_id)
    )
    items = result.scalars().all()
    item_ids = [item.id for item in items]
    
    if not item_ids:
        return []
    
    # Получаем все запросы с флагами
    result = await db.execute(
        select(SpendingRequest).where(
            SpendingRequest.spending_item_id.in_(item_ids),
            SpendingRequest.aml_flags.isnot(None)
        )
    )
    requests = result.scalars().all()
    
    flags_summary = []
    for request in requests:
        if request.aml_flags:
            flags_summary.append({
                "spending_request_id": request.id,
                "amount": str(request.amount),
                "flags": request.aml_flags,
                "status": request.status,
                "created_at": request.created_at.isoformat() if request.created_at else None
            })
    
    return flags_summary


"""
Роутер для работы со смарт-контрактом
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.schemas.contract import SmartContractLogResponse
from app.models.smart_contract_log import SmartContractOperationLog
from app.models.user import User
from app.utils.enums import UserRole
from sqlalchemy import select
from typing import List

router = APIRouter(prefix="/contract", tags=["Contract"])


@router.get("/logs", response_model=List[SmartContractLogResponse])
async def get_logs(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 100
):
    """Получение всех логов операций смарт-контракта"""
    result = await db.execute(
        select(SmartContractOperationLog)
        .order_by(SmartContractOperationLog.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [SmartContractLogResponse.model_validate(log) for log in logs]


@router.get("/logs/grant/{grant_id}", response_model=List[SmartContractLogResponse])
async def get_logs_by_grant(
    grant_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Получение логов операций по гранту"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Получаем все логи и фильтруем в Python
        # Это более надежный способ, так как JSON запросы могут быть сложными
        result = await db.execute(
            select(SmartContractOperationLog)
            .order_by(SmartContractOperationLog.timestamp.desc())
            .limit(1000)  # Ограничиваем для производительности
        )
        logs = result.scalars().all()
        
        # Фильтруем логи, где в payload есть grant_id
        filtered_logs = []
        for log in logs:
            if log.payload and isinstance(log.payload, dict):
                # Проверяем grant_id в payload (может быть строкой или числом)
                payload_grant_id = log.payload.get('grant_id')
                if payload_grant_id is not None:
                    # Преобразуем в int для сравнения
                    try:
                        if int(payload_grant_id) == grant_id:
                            filtered_logs.append(log)
                    except (ValueError, TypeError):
                        pass
        
        return [SmartContractLogResponse.model_validate(log) for log in filtered_logs]
    except Exception as e:
        logger.error(f"Error getting logs by grant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving logs: {str(e)}"
        )


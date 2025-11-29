"""
Роутер для университета
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.schemas.grant import GrantResponse, GrantDetailResponse
from app.schemas.spending import SpendingRequestResponse, SpendingRequestApprove
from app.schemas.contract import SmartContractLogResponse
from app.services.grant_service import grant_service
from app.services.spending_service import spending_service
from app.models.user import User
from app.models.smart_contract_log import SmartContractOperationLog
from app.utils.enums import UserRole
from sqlalchemy import select
from typing import List

router = APIRouter(prefix="/university", tags=["University"])


@router.get("/grants", response_model=List[GrantResponse])
async def get_university_grants(
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех грантов университета"""
    grants = await grant_service.get_grants_by_university(db, current_user.id)
    return [GrantResponse.model_validate(g) for g in grants]


@router.get("/grants/{grant_id}", response_model=GrantDetailResponse)
async def get_grant(
    grant_id: int,
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Получение гранта"""
    import logging
    from decimal import Decimal
    
    logger = logging.getLogger(__name__)
    
    try:
        grant = await grant_service.get_grant(db, grant_id)
        if not grant:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
        
        if grant.university_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        
        # Вычисляем remaining_amount
        remaining_amount = Decimal(str(grant.total_amount)) - Decimal(str(grant.amount_spent))
        
        # Создаем response с правильными данными
        response_data = {
            "id": grant.id,
            "title": grant.title,
            "total_amount": grant.total_amount,
            "amount_spent": grant.amount_spent,
            "university_id": grant.university_id,
            "state": grant.state,
            "created_at": grant.created_at,
            "remaining_amount": remaining_amount
        }
        
        return GrantDetailResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving grant: {str(e)}"
        )


@router.get("/grants/{grant_id}/requests", response_model=List[SpendingRequestResponse])
async def get_grant_requests(
    grant_id: int,
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Получение запросов по гранту"""
    grant = await grant_service.get_grant(db, grant_id)
    if not grant or grant.university_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Grant not found")
    
    from app.models.spending_item import SpendingItem
    from app.models.spending_request import SpendingRequest
    
    result = await db.execute(
        select(SpendingRequest)
        .join(SpendingItem)
        .where(SpendingItem.grant_id == grant_id)
    )
    requests = result.scalars().all()
    return [SpendingRequestResponse.model_validate(r) for r in requests]


@router.post("/requests/{request_id}/approve_top3", response_model=SpendingRequestResponse)
async def approve_top3_request(
    request_id: int,
    approval_data: SpendingRequestApprove,
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Одобрение/отклонение запроса из топ-3"""
    try:
        request = await spending_service.approve_request(
            db,
            request_id,
            current_user.id,
            approval_data.approved,
            approval_data.rejection_reason
        )
        return SpendingRequestResponse.model_validate(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/spending-requests", response_model=List[SpendingRequestResponse])
async def get_university_requests(
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех запросов на транш для университета"""
    from app.models.spending_item import SpendingItem
    from app.models.spending_request import SpendingRequest
    from app.models.grant import Grant
    
    # Получаем все гранты университета
    result = await db.execute(
        select(Grant).where(Grant.university_id == current_user.id)
    )
    grants = result.scalars().all()
    grant_ids = [g.id for g in grants]
    
    if not grant_ids:
        return []
    
    # Получаем все spending items для этих грантов
    result = await db.execute(
        select(SpendingItem).where(SpendingItem.grant_id.in_(grant_ids))
    )
    items = result.scalars().all()
    item_ids = [item.id for item in items]
    
    if not item_ids:
        return []
    
    # Получаем все запросы для этих items
    result = await db.execute(
        select(SpendingRequest).where(SpendingRequest.spending_item_id.in_(item_ids))
        .order_by(SpendingRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [SpendingRequestResponse.model_validate(r) for r in requests]


@router.get("/spending-requests/{request_id}", response_model=SpendingRequestResponse)
async def get_university_request(
    request_id: int,
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Получение одного запроса на транш для университета"""
    from app.models.spending_item import SpendingItem
    from app.models.spending_request import SpendingRequest
    from app.models.grant import Grant
    
    result = await db.execute(
        select(SpendingRequest).where(SpendingRequest.id == request_id)
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending request not found")
    
    # Проверяем, что запрос принадлежит гранту университета
    result = await db.execute(
        select(SpendingItem).where(SpendingItem.id == request.spending_item_id)
    )
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending item not found")
    
    result = await db.execute(
        select(Grant).where(Grant.id == item.grant_id)
    )
    grant = result.scalar_one_or_none()
    if not grant or grant.university_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return SpendingRequestResponse.model_validate(request)


@router.post("/approve-top3", status_code=status.HTTP_200_OK)
async def approve_top3(
    data: dict,
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db)
):
    """Одобрение топ-3 запросов"""
    request_ids = data.get("request_ids", [])
    if not request_ids:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="request_ids required")
    
    approved_requests = []
    for request_id in request_ids:
        try:
            approval_data = SpendingRequestApprove(approved=True)
            request = await spending_service.approve_request(
                db,
                request_id,
                current_user.id,
                approval_data.approved,
                approval_data.rejection_reason
            )
            approved_requests.append(SpendingRequestResponse.model_validate(request))
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error approving request {request_id}: {str(e)}"
            )
    
    return {"approved": len(approved_requests), "requests": approved_requests}


@router.get("/logs", response_model=List[SmartContractLogResponse])
async def get_logs(
    current_user: User = Depends(require_role(UserRole.UNIVERSITY)),
    db: AsyncSession = Depends(get_db),
    limit: int = 100
):
    """Получение логов операций"""
    result = await db.execute(
        select(SmartContractOperationLog)
        .order_by(SmartContractOperationLog.timestamp.desc())
        .limit(limit)
    )
    logs = result.scalars().all()
    return [SmartContractLogResponse.model_validate(log) for log in logs]


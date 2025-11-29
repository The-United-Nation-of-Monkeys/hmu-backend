"""
Роутер для грантополучателя
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.schemas.grant import GrantResponse
from app.schemas.spending import (
    SpendingItemCreate,
    SpendingItemResponse,
    SpendingRequestCreate,
    SpendingRequestResponse
)
from app.schemas.receipt import ReceiptResponse
from app.services.grant_service import grant_service
from app.services.spending_service import spending_service
from app.services.receipt_service import receipt_service
from app.models.user import User
from app.utils.enums import UserRole
from typing import List

router = APIRouter(prefix="/grantee", tags=["Grantee"])


@router.get("/grants", response_model=List[GrantResponse])
async def get_grants(
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Получение грантов грантополучателя"""
    grants = await grant_service.get_grants_by_grantee(db, current_user.id)
    return [GrantResponse.model_validate(g) for g in grants]


@router.post("/grants/{grant_id}/spending_items", response_model=List[SpendingItemResponse], status_code=status.HTTP_201_CREATED)
async def create_spending_items(
    grant_id: int,
    items: List[SpendingItemCreate],
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Создание мета-пунктов расходов"""
    try:
        created_items = await spending_service.create_spending_items(
            db, grant_id, items, current_user.id
        )
        return [SpendingItemResponse.model_validate(item) for item in created_items]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/spending_requests", response_model=SpendingRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_spending_request(
    request_data: SpendingRequestCreate,
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Создание запроса на транш"""
    try:
        request = await spending_service.create_spending_request(
            db, request_data, current_user.id
        )
        return SpendingRequestResponse.model_validate(request)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/spending-items", response_model=SpendingItemResponse, status_code=status.HTTP_201_CREATED)
async def create_spending_item(
    data: SpendingItemCreate,
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Создание одного мета-пункта расходов"""
    try:
        # Создаем временный объект SpendingItemCreate без grant_id для передачи в сервис
        from app.schemas.spending import SpendingItemCreate as ItemCreate
        item_data = ItemCreate(
            title=data.title,
            planned_amount=data.planned_amount,
            priority_index=data.priority_index
        )
        items = await spending_service.create_spending_items(
            db, data.grant_id, [item_data], current_user.id
        )
        if not items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create spending item")
        return SpendingItemResponse.model_validate(items[0])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/grants/{grant_id}/spending-items", response_model=List[SpendingItemResponse])
async def get_spending_items(
    grant_id: int,
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Получение мета-пунктов расходов по гранту"""
    from app.models.spending_item import SpendingItem
    from sqlalchemy import select
    
    result = await db.execute(
        select(SpendingItem).where(SpendingItem.grant_id == grant_id)
    )
    items = result.scalars().all()
    return [SpendingItemResponse.model_validate(item) for item in items]


@router.get("/spending-requests/{request_id}", response_model=SpendingRequestResponse)
async def get_spending_request(
    request_id: int,
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Получение одного запроса на транш"""
    from app.models.spending_request import SpendingRequest
    from sqlalchemy import select
    
    result = await db.execute(
        select(SpendingRequest).where(
            SpendingRequest.id == request_id,
            SpendingRequest.grantee_id == current_user.id
        )
    )
    request = result.scalar_one_or_none()
    if not request:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Spending request not found")
    return SpendingRequestResponse.model_validate(request)


@router.get("/spending-requests", response_model=List[SpendingRequestResponse])
async def get_spending_requests(
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех запросов на транш грантополучателя"""
    from app.models.spending_request import SpendingRequest
    from sqlalchemy import select
    
    result = await db.execute(
        select(SpendingRequest).where(SpendingRequest.grantee_id == current_user.id)
        .order_by(SpendingRequest.created_at.desc())
    )
    requests = result.scalars().all()
    return [SpendingRequestResponse.model_validate(r) for r in requests]


@router.post("/spending-requests/{request_id}/receipt", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt_new(
    request_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка чека (новый endpoint)"""
    # Проверка размера файла
    from app.core.config import settings
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large"
        )
    
    try:
        receipt = await receipt_service.upload_receipt(
            db, request_id, file_content, file.filename, current_user.id
        )
        return ReceiptResponse.model_validate(receipt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/spending_requests/{request_id}/upload_receipt", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    request_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка чека (старый endpoint для совместимости)"""
    # Проверка размера файла
    from app.core.config import settings
    file_content = await file.read()
    if len(file_content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large"
        )
    
    try:
        receipt = await receipt_service.upload_receipt(
            db, request_id, file_content, file.filename, current_user.id
        )
        return ReceiptResponse.model_validate(receipt)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


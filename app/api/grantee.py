"""
Роутер для грантополучателя
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.schemas.grant import GrantResponse, GrantDetailForGranteeResponse
from app.schemas.spending import (
    SpendingItemCreate,
    SpendingItemResponse,
    SpendingRequestCreate,
    SpendingRequestResponse
)
from app.schemas.receipt import ReceiptResponse, SpendingItemReceiptResponse
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


@router.get("/grants/{grant_id}", response_model=GrantDetailForGranteeResponse)
async def get_grant_detail(
    grant_id: int,
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Получение детальной информации о гранте с вложенными данными"""
    import logging
    from app.models.spending_item import SpendingItem
    from app.models.spending_request import SpendingRequest
    from app.models.receipt import Receipt
    from sqlalchemy import select
    import os
    
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка существования гранта
        grant = await grant_service.get_grant(db, grant_id)
        if not grant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        # Проверка, что грант назначен на текущего грантополучателя
        if grant.grantee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Grant is not assigned to you"
            )
        
        # Получение всех SpendingItem для данного гранта
        result = await db.execute(
            select(SpendingItem)
            .where(SpendingItem.grant_id == grant_id)
            .order_by(SpendingItem.priority_index.asc())
        )
        items = result.scalars().all()
        
        # Получение всех SpendingRequest для данного гранта
        result = await db.execute(
            select(SpendingRequest)
            .join(SpendingItem)
            .where(SpendingItem.grant_id == grant_id)
            .where(SpendingRequest.grantee_id == current_user.id)
            .order_by(SpendingRequest.created_at.desc())
        )
        requests = result.scalars().all()
        
        # Получение чеков для spending items
        item_ids = [item.id for item in items]
        receipts_for_items = {}
        if item_ids:
            result = await db.execute(
                select(Receipt)
                .where(Receipt.spending_item_id.in_(item_ids))
            )
            receipts = result.scalars().all()
            for receipt in receipts:
                if receipt.spending_item_id:
                    receipts_for_items[receipt.spending_item_id] = receipt
        
        # Получение чеков для spending requests
        request_ids = [req.id for req in requests]
        receipts_for_requests = {}
        if request_ids:
            result = await db.execute(
                select(Receipt)
                .where(Receipt.spending_request_id.in_(request_ids))
            )
            receipts = result.scalars().all()
            for receipt in receipts:
                if receipt.spending_request_id:
                    receipts_for_requests[receipt.spending_request_id] = receipt
        
        # Формирование spending_items с чеками
        spending_items_data = []
        for item in items:
            receipt = receipts_for_items.get(item.id)
            receipt_url = None
            if receipt:
                filename = os.path.basename(receipt.file_path) if receipt.file_path else ""
                receipt_url = f"/api/files/{filename}" if filename else None
            
            spending_items_data.append({
                "id": item.id,
                "grant_id": item.grant_id,
                "title": item.title,
                "description": None,  # Поле description пока не в модели
                "amount": str(item.planned_amount),
                "receipt_url": receipt_url,
                "created_at": None  # Поле created_at пока не в модели
            })
        
        # Формирование spending_requests с чеками
        spending_requests_data = []
        for req in requests:
            receipt = receipts_for_requests.get(req.id)
            receipt_url = None
            if receipt:
                filename = os.path.basename(receipt.file_path) if receipt.file_path else ""
                receipt_url = f"/api/files/{filename}" if filename else None
            
            spending_requests_data.append({
                "id": req.id,
                "grant_id": grant_id,
                "spending_item_id": req.spending_item_id,
                "amount": str(req.amount),
                "status": req.status,
                "created_at": req.created_at.isoformat() if req.created_at else None,
                "updated_at": req.updated_at.isoformat() if req.updated_at else None,
                "receipt_url": receipt_url,
                "aml_flags": req.aml_flags or []
            })
        
        # Формирование ответа
        response_data = {
            "id": grant.id,
            "title": grant.title,
            "total_amount": grant.total_amount,
            "amount_spent": grant.amount_spent,
            "university_id": grant.university_id,
            "grantee_id": grant.grantee_id,
            "state": grant.state,
            "created_at": grant.created_at,
            "spending_items": spending_items_data,
            "spending_requests": spending_requests_data
        }
        
        return GrantDetailForGranteeResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grant detail: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving grant detail: {str(e)}"
        )


@router.post("/grants/{grant_id}/spending-items", response_model=List[SpendingItemResponse], status_code=status.HTTP_201_CREATED)
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


@router.post("/spending-requests", response_model=SpendingRequestResponse, status_code=status.HTTP_201_CREATED)
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
    import logging
    from app.models.spending_item import SpendingItem
    from app.models.grant import Grant
    from sqlalchemy import select
    
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка существования гранта
        grant = await grant_service.get_grant(db, grant_id)
        if not grant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        # Проверка, что грант назначен на текущего грантополучателя
        if grant.grantee_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Grant is not assigned to you"
            )
        
        # Получение всех SpendingItem для данного гранта
        result = await db.execute(
            select(SpendingItem)
            .where(SpendingItem.grant_id == grant_id)
            .order_by(SpendingItem.priority_index.asc())
        )
        items = result.scalars().all()
        
        # Преобразуем в response формат
        response_items = []
        for item in items:
            item_data = {
                "id": item.id,
                "grant_id": item.grant_id,
                "title": item.title,
                "description": None,  # Поле description пока не в модели
                "planned_amount": item.planned_amount,
                "priority_index": item.priority_index,
                "created_at": None  # Поле created_at пока не в модели
            }
            response_items.append(SpendingItemResponse(**item_data))
        
        return response_items
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting spending items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving spending items: {str(e)}"
        )


@router.post("/spending-items/{spending_item_id}/receipt", response_model=SpendingItemReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt_for_spending_item(
    spending_item_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка чека для статьи расходов"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Чтение файла
        file_content = await file.read()
        
        # Загрузка чека через сервис
        receipt = await receipt_service.upload_receipt_for_spending_item(
            db,
            spending_item_id,
            file_content,
            file.filename,
            current_user.id
        )
        
        return SpendingItemReceiptResponse.model_validate(receipt)
    except ValueError as e:
        logger.error(f"Validation error uploading receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading receipt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading receipt: {str(e)}"
        )


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


@router.post("/spending-requests/{request_id}/upload-receipt", response_model=ReceiptResponse, status_code=status.HTTP_201_CREATED)
async def upload_receipt(
    request_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.GRANTEE)),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка чека для запроса на транш"""
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка размера файла
        from app.core.config import settings
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File too large"
            )
        
        receipt = await receipt_service.upload_receipt(
            db, request_id, file_content, file.filename, current_user.id
        )
        return ReceiptResponse.model_validate(receipt)
    except ValueError as e:
        logger.error(f"Validation error uploading receipt: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading receipt: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error uploading receipt: {str(e)}"
        )


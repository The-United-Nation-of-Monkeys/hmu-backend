"""
Роутер для правительства
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.base import get_db
from app.api.dependencies import require_role, get_current_user
from app.schemas.grant import GrantCreate, GrantResponse, GrantDetailWithItemsResponse
from app.schemas.spending import SpendingItemResponse
from app.services.grant_service import grant_service
from app.services.spending_service import spending_service
from app.utils.enums import UserRole
from app.models.user import User
from typing import List

router = APIRouter(prefix="/government", tags=["Government"])


@router.get("/grants", response_model=List[GrantResponse])
async def get_all_grants(
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех грантов"""
    grants = await grant_service.get_all_grants(db)
    return [GrantResponse.model_validate(g) for g in grants]


@router.get("/grants/{grant_id}", response_model=GrantDetailWithItemsResponse)
async def get_grant(
    grant_id: int,
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Получение гранта по ID с spending items и requests"""
    import logging
    from decimal import Decimal
    from app.models.spending_item import SpendingItem
    from app.models.spending_request import SpendingRequest
    from app.models.receipt import Receipt
    from sqlalchemy import select
    import os
    
    logger = logging.getLogger(__name__)
    
    try:
        grant = await grant_service.get_grant(db, grant_id)
        if not grant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        # Вычисляем remaining_amount
        remaining_amount = Decimal(str(grant.total_amount)) - Decimal(str(grant.amount_spent))
        
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
                "description": None,
                "amount": str(item.planned_amount),
                "receipt_url": receipt_url,
                "created_at": None
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
            "remaining_amount": remaining_amount,
            "spending_items": spending_items_data,
            "spending_requests": spending_requests_data
        }
        
        return GrantDetailWithItemsResponse(**response_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting grant: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving grant: {str(e)}"
        )


@router.post("/grants", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
async def create_grant(
    grant_data: GrantCreate,
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Создание гранта"""
    import logging
    import traceback
    
    logger = logging.getLogger(__name__)
    
    try:
        grant = await grant_service.create_grant(db, grant_data, current_user.id)
        return GrantResponse.model_validate(grant)
    except ValueError as e:
        logger.error(f"Validation error creating grant: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating grant: {e}\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/universities", response_model=List[dict])
async def get_universities(
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Получение списка университетов"""
    from sqlalchemy import select
    from app.utils.enums import UserRole
    
    result = await db.execute(
        select(User).where(User.role == UserRole.UNIVERSITY).order_by(User.name)
    )
    universities = result.scalars().all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email
        }
        for u in universities
    ]


@router.get("/transactions", response_model=List[dict])
async def get_transactions(
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Получение всех транзакций"""
    from app.models.transaction import Transaction
    from sqlalchemy import select
    
    result = await db.execute(
        select(Transaction).order_by(Transaction.created_at.desc())
    )
    transactions = result.scalars().all()
    return [
        {
            "id": t.id,
            "spending_request_id": t.spending_request_id,
            "source": t.source,
            "destination": t.destination,
            "amount": str(t.amount),
            "currency": t.currency,
            "external_id": t.external_id,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in transactions
    ]


@router.post("/grants/{grant_id}/spending-items/upload", status_code=status.HTTP_201_CREATED)
async def upload_spending_items(
    grant_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(require_role(UserRole.GOVERNMENT)),
    db: AsyncSession = Depends(get_db)
):
    """Загрузка Excel/CSV файла со статьями расходов"""
    import logging
    from pathlib import Path
    
    logger = logging.getLogger(__name__)
    
    try:
        # Проверка существования гранта
        grant = await grant_service.get_grant(db, grant_id)
        if not grant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Grant not found"
            )
        
        # Валидация формата файла
        file_ext = Path(file.filename).suffix.lower()
        allowed_extensions = {'.xlsx', '.xls', '.csv'}
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid file format. Allowed: {', '.join(allowed_extensions)}"
            )
        
        # Чтение файла
        file_content = await file.read()
        
        # Создание spending items из файла
        created_items = await spending_service.create_spending_items_from_file(
            db,
            grant_id,
            file_content,
            file.filename
        )
        
        # Формирование ответа
        items_response = []
        for item in created_items:
            item_data = {
                "id": item.id,
                "grant_id": item.grant_id,
                "title": item.title,
                "description": None,  # Поле description пока не в модели
                "planned_amount": item.planned_amount,
                "priority_index": item.priority_index,
                "created_at": None  # Поле created_at пока не в модели
            }
            items_response.append(SpendingItemResponse(**item_data))
        
        logger.info(f"Created {len(created_items)} spending items from file for grant {grant_id}")
        
        return {
            "created": len(created_items),
            "items": items_response
        }
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error uploading spending items: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error uploading spending items: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )


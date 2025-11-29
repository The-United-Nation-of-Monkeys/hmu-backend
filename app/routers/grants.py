"""
Роутер для работы с грантами
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.grant import GrantCreate, GrantResponse, GrantReport
from app.models.grant import Grant
from app.services.report_service import report_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/grants", response_model=GrantResponse, status_code=status.HTTP_201_CREATED)
async def create_grant(
    grant_data: GrantCreate,
    db: Session = Depends(get_db)
):
    """
    Создание нового гранта
    """
    try:
        grant = Grant(
            title=grant_data.title,
            amount_total=grant_data.amount_total,
            grantee_id=grant_data.grantee_id,
            blockchain_address=grant_data.blockchain_address,
            amount_spent=0
        )
        
        db.add(grant)
        db.commit()
        db.refresh(grant)
        
        return GrantResponse.model_validate(grant)
        
    except Exception as e:
        logger.error(f"Ошибка создания гранта: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания гранта: {str(e)}"
        )


@router.get("/grants", response_model=List[GrantResponse])
async def list_grants(
    grantee_id: int = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Список грантов
    """
    query = db.query(Grant)
    
    if grantee_id:
        query = query.filter(Grant.grantee_id == grantee_id)
    
    grants = query.offset(skip).limit(limit).all()
    return [GrantResponse.model_validate(g) for g in grants]


@router.get("/grants/{grant_id}", response_model=GrantResponse)
async def get_grant(
    grant_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение гранта по ID
    """
    grant = db.query(Grant).filter(Grant.id == grant_id).first()
    if not grant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Грант {grant_id} не найден"
        )
    return GrantResponse.from_orm(grant)


@router.get("/grants/{grant_id}/report", response_model=GrantReport)
async def get_grant_report(
    grant_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение отчёта по гранту
    
    Возвращает:
    - Общий бюджет и потраченную сумму
    - Разбивку по категориям
    - Список подозрительных расходов
    - Статистику по статусам
    - Hash из блокчейна
    """
    try:
        report = report_service.generate_grant_report(db, grant_id)
        return report
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


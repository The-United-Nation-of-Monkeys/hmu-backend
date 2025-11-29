"""
Роутер для работы с расходами
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.schemas.expense import ExpenseCreate, ExpenseResponse, ExpenseManualCreate, ExpenseUpdate
from app.models.expense import Expense, ExpenseStatus
from app.services.expense_service import expense_service
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/expenses/manual", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
async def create_manual_expense(
    expense_data: ExpenseManualCreate,
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    """
    Создание расхода вручную с загрузкой файла (чека)
    
    Args:
        expense_data: Данные расхода
        file: Файл чека (PDF/JPEG)
        db: Сессия БД
    """
    try:
        # В реальности здесь должна быть обработка файла
        # Сохранение в хранилище, OCR для извлечения данных и т.д.
        if file:
            logger.info(f"Получен файл: {file.filename}, размер: {file.size}")
            # TODO: Сохранить файл и обработать
        
        expense = expense_service.create_manual_expense(
            db=db,
            grant_id=expense_data.grant_id,
            amount=expense_data.amount,
            description=expense_data.description,
            category=expense_data.category
        )
        
        return ExpenseResponse.model_validate(expense)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Ошибка создания расхода: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка создания расхода: {str(e)}"
        )


@router.get("/expenses", response_model=List[ExpenseResponse])
async def list_expenses(
    grant_id: int = None,
    status: ExpenseStatus = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    Список расходов с фильтрацией
    """
    query = db.query(Expense)
    
    if grant_id:
        query = query.filter(Expense.grant_id == grant_id)
    if status:
        query = query.filter(Expense.status == status)
    
    expenses = query.offset(skip).limit(limit).all()
    return [ExpenseResponse.model_validate(e) for e in expenses]


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: int,
    db: Session = Depends(get_db)
):
    """
    Получение расхода по ID
    """
    expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not expense:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Расход {expense_id} не найден"
        )
    return ExpenseResponse.from_orm(expense)


@router.patch("/expenses/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    update_data: ExpenseUpdate,
    db: Session = Depends(get_db)
):
    """
    Обновление расхода (статус, комментарий)
    """
    try:
        expense = expense_service.update_expense_status(
            db=db,
            expense_id=expense_id,
            status=update_data.status,
            comment=update_data.comment
        )
        return ExpenseResponse.model_validate(expense)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


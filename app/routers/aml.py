"""
Роутер для AML проверок
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.aml import AMLCheckRequest, AMLCheckResponse
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.grant import Grant
from app.models.user import User
from app.services.aml_engine import aml_engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/aml/check", response_model=AMLCheckResponse)
async def check_aml(
    request: AMLCheckRequest,
    db: Session = Depends(get_db)
):
    """
    Ручная AML проверка
    
    Проверяет транзакцию/расход на AML нарушения
    """
    try:
        # Получаем данные
        transaction = None
        expense = None
        
        if request.transaction_id:
            transaction = db.query(Transaction).filter(
                Transaction.id == request.transaction_id
            ).first()
        
        if request.expense_id:
            expense = db.query(Expense).filter(
                Expense.id == request.expense_id
            ).first()
            if expense and not transaction and expense.transaction_id:
                transaction = db.query(Transaction).filter(
                    Transaction.id == expense.transaction_id
                ).first()
        
        grant = db.query(Grant).filter(Grant.id == request.grant_id).first()
        if not grant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Грант {request.grant_id} не найден"
            )
        
        user = None
        if request.grantee_name:
            # Ищем пользователя по имени
            user = db.query(User).filter(User.name == request.grantee_name).first()
        elif grant:
            user = db.query(User).filter(User.id == grant.grantee_id).first()
        
        # Создаём временный expense для проверки, если его нет
        if not expense:
            from app.models.expense import Expense as ExpenseModel
            expense = ExpenseModel(
                grant_id=request.grant_id,
                amount=request.amount,
                category=None
            )
        
        # Выполняем проверку
        flags = aml_engine.check(transaction, expense, user, grant)
        
        # Определяем рекомендацию
        is_suspicious = len(flags) > 0
        if not flags:
            recommendation = "approve"
        elif len(flags) == 1 and "no_receipt" in flags:
            recommendation = "review"
        else:
            recommendation = "reject"
        
        return AMLCheckResponse(
            flags=flags,
            is_suspicious=is_suspicious,
            recommendation=recommendation
        )
        
    except Exception as e:
        logger.error(f"Ошибка AML проверки: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка AML проверки: {str(e)}"
        )


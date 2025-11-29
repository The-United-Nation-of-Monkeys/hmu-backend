"""
Роутер для webhook от МИР
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.schemas.transaction import MirWebhookRequest, TransactionResponse
from app.models.transaction import Transaction
from app.models.grant import Grant
from app.services.expense_service import expense_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/mir/webhook", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def mir_webhook(
    request: MirWebhookRequest,
    db: Session = Depends(get_db)
):
    """
    Webhook для получения транзакций от МИР
    
    Логика:
    1. Сохранить транзакцию
    2. Найти грант по grantee_id (нужно добавить логику определения гранта)
    3. Создать расход
    4. Запустить AML проверку
    5. Записать в блокчейн
    """
    try:
        # Проверяем, не существует ли уже такая транзакция
        existing = db.query(Transaction).filter(
            Transaction.mir_id == request.transaction_id
        ).first()
        
        if existing:
            logger.warning(f"Транзакция {request.transaction_id} уже существует")
            return TransactionResponse.model_validate(existing)
        
        # Создаём транзакцию
        transaction = Transaction(
            mir_id=request.transaction_id,
            amount=request.amount,
            mcc_code=request.mcc,
            merchant_name=request.merchant,
            has_receipt=request.receipt is not None,
            raw_receipt_json=request.receipt
        )
        
        db.add(transaction)
        db.commit()
        db.refresh(transaction)
        
        # TODO: Логика определения гранта по транзакции
        # Для прототипа берём первый активный грант
        # В реальности нужна привязка карты/счёта к гранту
        grant = db.query(Grant).first()
        
        if not grant:
            logger.warning("Грант не найден, транзакция сохранена без привязки")
            return TransactionResponse.model_validate(transaction)
        
        # Создаём расход из транзакции
        try:
            expense = expense_service.create_expense_from_transaction(
                db, transaction, grant.id
            )
            logger.info(
                f"Расход {expense.id} создан из транзакции {transaction.id}, "
                f"статус: {expense.status}, флаги AML: {expense.aml_flags}"
            )
        except Exception as e:
            logger.error(f"Ошибка создания расхода: {e}")
            # Транзакция уже сохранена, продолжаем
        
        return TransactionResponse.model_validate(transaction)
        
    except Exception as e:
        logger.error(f"Ошибка обработки webhook МИР: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка обработки транзакции: {str(e)}"
        )


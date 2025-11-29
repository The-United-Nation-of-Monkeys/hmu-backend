"""
Сервис для работы с расходами
"""
from sqlalchemy.orm import Session
from sqlalchemy import and_
from app.models.expense import Expense, ExpenseStatus
from app.models.transaction import Transaction
from app.models.grant import Grant
from app.models.user import User
from app.services.aml_engine import aml_engine
from app.services.blockchain import blockchain_service
from decimal import Decimal
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ExpenseService:
    """Сервис для управления расходами"""
    
    @staticmethod
    def create_expense_from_transaction(
        db: Session,
        transaction: Transaction,
        grant_id: int
    ) -> Expense:
        """
        Создание расхода из транзакции МИР
        
        Args:
            db: Сессия БД
            transaction: Транзакция от МИР
            grant_id: ID гранта
            
        Returns:
            Созданный расход
        """
        # Получаем грант и пользователя
        grant = db.query(Grant).filter(Grant.id == grant_id).first()
        if not grant:
            raise ValueError(f"Грант {grant_id} не найден")
        
        user = db.query(User).filter(User.id == grant.grantee_id).first()
        
        # Создаём расход
        expense = Expense(
            grant_id=grant_id,
            transaction_id=transaction.id,
            amount=transaction.amount,
            category=transaction.mcc_code,
            status=ExpenseStatus.PENDING
        )
        
        # AML проверка
        aml_flags = aml_engine.check(transaction, expense, user, grant)
        
        # Проверка дубликатов
        if aml_engine.check_duplicates(
            db, grant_id, transaction.amount, transaction.id
        ):
            aml_flags.append("duplicated_transactions")
        
        expense.aml_flags = aml_flags
        
        # Определяем статус на основе AML флагов
        if not aml_flags:
            expense.status = ExpenseStatus.APPROVED
            # Обновляем потраченную сумму гранта
            grant.amount_spent += transaction.amount
        else:
            expense.status = ExpenseStatus.MANUAL_REVIEW
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        # Логируем в блокчейн
        if grant.blockchain_address:
            try:
                tx_hash = blockchain_service.log_expense(
                    grant.blockchain_address,
                    expense.id,
                    float(expense.amount),
                    expense.category
                )
                logger.info(f"Расход {expense.id} записан в блокчейн: {tx_hash}")
            except Exception as e:
                logger.error(f"Ошибка записи в блокчейн: {e}")
        
        return expense
    
    @staticmethod
    def create_manual_expense(
        db: Session,
        grant_id: int,
        amount: Decimal,
        description: Optional[str] = None,
        category: Optional[str] = None
    ) -> Expense:
        """
        Создание расхода вручную
        
        Args:
            db: Сессия БД
            grant_id: ID гранта
            amount: Сумма
            description: Описание
            category: Категория
            
        Returns:
            Созданный расход
        """
        grant = db.query(Grant).filter(Grant.id == grant_id).first()
        if not grant:
            raise ValueError(f"Грант {grant_id} не найден")
        
        expense = Expense(
            grant_id=grant_id,
            transaction_id=None,
            amount=amount,
            category=category,
            status=ExpenseStatus.MANUAL_REVIEW,
            comment=description
        )
        
        db.add(expense)
        db.commit()
        db.refresh(expense)
        
        return expense
    
    @staticmethod
    def update_expense_status(
        db: Session,
        expense_id: int,
        status: ExpenseStatus,
        comment: Optional[str] = None
    ) -> Expense:
        """
        Обновление статуса расхода
        
        Args:
            db: Сессия БД
            expense_id: ID расхода
            status: Новый статус
            comment: Комментарий
            
        Returns:
            Обновлённый расход
        """
        expense = db.query(Expense).filter(Expense.id == expense_id).first()
        if not expense:
            raise ValueError(f"Расход {expense_id} не найден")
        
        old_status = expense.status
        expense.status = status
        if comment:
            expense.comment = comment
        
        # Если статус изменился на APPROVED, обновляем сумму гранта
        if old_status != ExpenseStatus.APPROVED and status == ExpenseStatus.APPROVED:
            grant = db.query(Grant).filter(Grant.id == expense.grant_id).first()
            if grant:
                grant.amount_spent += expense.amount
        
        # Если статус изменился с APPROVED на другой, вычитаем сумму
        if old_status == ExpenseStatus.APPROVED and status != ExpenseStatus.APPROVED:
            grant = db.query(Grant).filter(Grant.id == expense.grant_id).first()
            if grant:
                grant.amount_spent -= expense.amount
        
        db.commit()
        db.refresh(expense)
        
        return expense


# Глобальный экземпляр сервиса
expense_service = ExpenseService()


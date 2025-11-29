"""
Сервис для генерации отчётов
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.grant import Grant
from app.models.expense import Expense, ExpenseStatus
from app.schemas.grant import GrantReport
from app.services.blockchain import blockchain_service
from decimal import Decimal
from typing import Dict


class ReportService:
    """Сервис для генерации отчётов по грантам"""
    
    @staticmethod
    def generate_grant_report(db: Session, grant_id: int) -> GrantReport:
        """
        Генерация отчёта по гранту
        
        Args:
            db: Сессия БД
            grant_id: ID гранта
            
        Returns:
            Отчёт по гранту
        """
        grant = db.query(Grant).filter(Grant.id == grant_id).first()
        if not grant:
            raise ValueError(f"Грант {grant_id} не найден")
        
        # Получаем все расходы
        expenses = db.query(Expense).filter(Expense.grant_id == grant_id).all()
        
        # Подсчёт по статусам
        approved_count = sum(1 for e in expenses if e.status == ExpenseStatus.APPROVED)
        rejected_count = sum(1 for e in expenses if e.status == ExpenseStatus.REJECTED)
        pending_count = sum(1 for e in expenses if e.status == ExpenseStatus.PENDING)
        manual_review_count = sum(1 for e in expenses if e.status == ExpenseStatus.MANUAL_REVIEW)
        suspicious_count = sum(1 for e in expenses if e.aml_flags)
        
        # Подсчёт по категориям
        categories_breakdown: Dict[str, Decimal] = {}
        for expense in expenses:
            if expense.status == ExpenseStatus.APPROVED:
                category = expense.category or "Без категории"
                if category not in categories_breakdown:
                    categories_breakdown[category] = Decimal(0)
                categories_breakdown[category] += expense.amount
        
        # Подсчёт сумм
        total_budget = Decimal(str(grant.amount_total))
        spent = Decimal(str(grant.amount_spent))
        remaining = total_budget - spent
        
        # Проценты
        funded_percentage = float((spent / total_budget * 100) if total_budget > 0 else 0)
        rejected_percentage = float((rejected_count / len(expenses) * 100) if expenses else 0)
        
        # Получаем hash из блокчейна (mock для прототипа)
        blockchain_hash = None
        if grant.blockchain_address:
            # В реальности здесь должен быть запрос к блокчейну
            blockchain_hash = f"0x{grant_id:064x}"
        
        return GrantReport(
            grant_id=grant.id,
            title=grant.title,
            total_budget=total_budget,
            spent=spent,
            remaining=remaining,
            categories_breakdown=categories_breakdown,
            suspicious_expenses_count=suspicious_count,
            approved_expenses_count=approved_count,
            rejected_expenses_count=rejected_count,
            pending_expenses_count=pending_count,
            funded_percentage=funded_percentage,
            rejected_percentage=rejected_percentage,
            blockchain_hash=blockchain_hash
        )


# Глобальный экземпляр сервиса
report_service = ReportService()


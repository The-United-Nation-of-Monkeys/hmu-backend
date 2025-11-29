"""
AML движок
"""
from typing import List
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.spending_request import SpendingRequest
from app.models.grant import Grant
from app.models.user import User
from app.core.config import settings
from datetime import datetime, timedelta
import re


class AMLEngine:
    """Движок для AML проверок"""
    
    @staticmethod
    async def check_spending_request(
        db: AsyncSession,
        spending_request: SpendingRequest,
        grant: Grant,
        grantee: User
    ) -> List[str]:
        """
        Проверка запроса на транш на AML нарушения
        
        Returns:
            Список флагов AML
        """
        flags = []
        
        # 1. Проверка большой суммы (>20% от гранта)
        if grant.total_amount > 0:
            threshold = float(grant.total_amount) * settings.AML_LARGE_AMOUNT_THRESHOLD
            if float(spending_request.amount) > threshold:
                flags.append("large_amount")
        
        # 2. Проверка дубликатов
        time_threshold = datetime.utcnow() - timedelta(minutes=settings.AML_DUPLICATE_WINDOW_MINUTES)
        result = await db.execute(
            select(SpendingRequest).where(
                and_(
                    SpendingRequest.grantee_id == spending_request.grantee_id,
                    SpendingRequest.amount == spending_request.amount,
                    SpendingRequest.created_at >= time_threshold,
                    SpendingRequest.id != spending_request.id
                )
            )
        )
        duplicates = result.scalars().all()
        if duplicates:
            flags.append("duplicated_transactions")
        
        # 3. Проверка превышения бюджета
        if float(grant.amount_spent) + float(spending_request.amount) > float(grant.total_amount):
            flags.append("budget_exceeded")
        
        return flags
    
    @staticmethod
    def check_receipt_required(spending_request: SpendingRequest) -> bool:
        """Проверка, требуется ли чек"""
        # Если предыдущий запрос оплачен, но чек не загружен
        return spending_request.status.value == "pending_receipt"


aml_engine = AMLEngine()


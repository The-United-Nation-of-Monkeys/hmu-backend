"""
Адаптер для платёжной системы (МИР) - mock
"""
from typing import Dict, Any
from decimal import Decimal
import uuid


class PaymentAdapter:
    """Mock адаптер для платёжной системы МИР"""
    
    @staticmethod
    async def execute_payment(
        source: str,
        destination: str,
        amount: Decimal,
        currency: str = "RUB"
    ) -> Dict[str, Any]:
        """
        Выполнение платежа через МИР (mock)
        
        Returns:
            Словарь с данными транзакции
        """
        # Mock реализация
        transaction_id = f"MIR-{uuid.uuid4().hex[:16].upper()}"
        
        return {
            "transaction_id": transaction_id,
            "status": "success",
            "amount": str(amount),
            "currency": currency,
            "source": source,
            "destination": destination,
            "timestamp": "2024-01-01T00:00:00Z"
        }
    
    @staticmethod
    async def get_transaction_status(transaction_id: str) -> Dict[str, Any]:
        """Получение статуса транзакции"""
        return {
            "transaction_id": transaction_id,
            "status": "completed",
            "confirmed": True
        }


payment_adapter = PaymentAdapter()


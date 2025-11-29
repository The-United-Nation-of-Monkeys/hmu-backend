"""
Сервис для работы со смарт-контрактом (mock adapter)
"""
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.smart_contract_log import SmartContractOperationLog
from app.utils.enums import OperationType
import json
import hashlib


class SmartContractService:
    """Сервис для работы со смарт-контрактом (mock)"""
    
    @staticmethod
    async def log_operation(
        db: AsyncSession,
        operation_type: OperationType,
        payload: Dict[str, Any],
        result: Optional[str] = None
    ) -> SmartContractOperationLog:
        """
        Логирование операции в смарт-контракт
        
        Args:
            db: Сессия БД
            operation_type: Тип операции
            payload: Данные операции
            result: Результат операции
            
        Returns:
            Лог операции
        """
        # Генерация mock tx_hash
        tx_hash = f"0x{hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:64]}"
        
        # Преобразуем payload в JSON-совместимый формат
        json_payload = json.loads(json.dumps(payload, default=str))
        
        log = SmartContractOperationLog(
            operation_type=operation_type.value if hasattr(operation_type, 'value') else str(operation_type),
            payload=json_payload,
            result=result,
            tx_hash=tx_hash
        )
        
        db.add(log)
        await db.commit()
        await db.refresh(log)
        
        return log
    
    @staticmethod
    async def create_grant(
        db: AsyncSession,
        grant_id: int,
        total_amount: float,
        university_id: int
    ) -> SmartContractOperationLog:
        """Создание гранта в смарт-контракте"""
        payload = {
            "grant_id": grant_id,
            "total_amount": str(total_amount),
            "university_id": university_id
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.GRANT_CREATED,
            payload,
            "Grant created successfully"
        )
    
    @staticmethod
    async def create_spending_request(
        db: AsyncSession,
        request_id: int,
        spending_item_id: int,
        amount: float
    ) -> SmartContractOperationLog:
        """Создание запроса на транш в смарт-контракте"""
        payload = {
            "request_id": request_id,
            "spending_item_id": spending_item_id,
            "amount": str(amount)
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.SPENDING_REQUEST_CREATED,
            payload,
            "Spending request created"
        )
    
    @staticmethod
    async def approve_spending_request(
        db: AsyncSession,
        request_id: int,
        approved_by: int
    ) -> SmartContractOperationLog:
        """Одобрение запроса в смарт-контракте"""
        payload = {
            "request_id": request_id,
            "approved_by": approved_by
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.SPENDING_REQUEST_APPROVED,
            payload,
            "Spending request approved"
        )
    
    @staticmethod
    async def reject_spending_request(
        db: AsyncSession,
        request_id: int,
        reason: str
    ) -> SmartContractOperationLog:
        """Отклонение запроса в смарт-контракте"""
        payload = {
            "request_id": request_id,
            "reason": reason
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.SPENDING_REQUEST_REJECTED,
            payload,
            f"Spending request rejected: {reason}"
        )
    
    @staticmethod
    async def execute_payment(
        db: AsyncSession,
        request_id: int,
        amount: float,
        transaction_id: str
    ) -> SmartContractOperationLog:
        """Выполнение платежа в смарт-контракте"""
        payload = {
            "request_id": request_id,
            "amount": str(amount),
            "transaction_id": transaction_id
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.PAYMENT_EXECUTED,
            payload,
            "Payment executed"
        )
    
    @staticmethod
    async def verify_receipt(
        db: AsyncSession,
        request_id: int,
        receipt_id: int
    ) -> SmartContractOperationLog:
        """Верификация чека в смарт-контракте"""
        payload = {
            "request_id": request_id,
            "receipt_id": receipt_id
        }
        return await SmartContractService.log_operation(
            db,
            OperationType.RECEIPT_VERIFIED,
            payload,
            "Receipt verified"
        )


smart_contract_service = SmartContractService()


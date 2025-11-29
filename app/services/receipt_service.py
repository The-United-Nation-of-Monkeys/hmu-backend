"""
Сервис для работы с чеками
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.receipt import Receipt
from app.models.spending_request import SpendingRequest
from app.services.smart_contract_service import smart_contract_service
from app.utils.enums import SpendingRequestStatus
import os
import uuid
from pathlib import Path


class ReceiptService:
    """Сервис для управления чеками"""
    
    @staticmethod
    async def upload_receipt(
        db: AsyncSession,
        spending_request_id: int,
        file_content: bytes,
        filename: str,
        uploaded_by: int
    ) -> Receipt:
        """Загрузка чека"""
        # Проверка запроса
        result = await db.execute(
            select(SpendingRequest).where(SpendingRequest.id == spending_request_id)
        )
        request = result.scalar_one_or_none()
        if not request:
            raise ValueError("Spending request not found")
        
        if request.status != SpendingRequestStatus.PENDING_RECEIPT.value:
            raise ValueError("Request is not in pending_receipt status")
        
        # Проверка существующего чека
        result = await db.execute(
            select(Receipt).where(Receipt.spending_request_id == spending_request_id)
        )
        existing_receipt = result.scalar_one_or_none()
        if existing_receipt:
            raise ValueError("Receipt already exists for this request")
        
        # Сохранение файла
        from app.core.config import settings
        upload_dir = Path(settings.UPLOAD_DIR)
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_ext = Path(filename).suffix
        file_name = f"{spending_request_id}_{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / file_name
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Создание записи
        receipt = Receipt(
            spending_request_id=spending_request_id,
            file_path=str(file_path),
            uploaded_by=uploaded_by,
            verified=False
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        
        return receipt
    
    @staticmethod
    async def verify_receipt(
        db: AsyncSession,
        receipt_id: int,
        verified: bool = True
    ) -> Receipt:
        """Верификация чека"""
        result = await db.execute(select(Receipt).where(Receipt.id == receipt_id))
        receipt = result.scalar_one_or_none()
        if not receipt:
            raise ValueError("Receipt not found")
        
        receipt.verified = verified
        if verified:
            from datetime import datetime
            receipt.verified_at = datetime.utcnow()
            
            # Обновление статуса запроса
            result = await db.execute(
                select(SpendingRequest).where(SpendingRequest.id == receipt.spending_request_id)
            )
            request = result.scalar_one_or_none()
            if request:
                request.status = SpendingRequestStatus.PAID.value
            
            # Логирование в смарт-контракт
            await smart_contract_service.verify_receipt(db, request.id, receipt.id)
        
        await db.commit()
        await db.refresh(receipt)
        return receipt


receipt_service = ReceiptService()


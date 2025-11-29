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


    @staticmethod
    async def upload_receipt_for_spending_item(
        db: AsyncSession,
        spending_item_id: int,
        file_content: bytes,
        filename: str,
        uploaded_by: int
    ) -> Receipt:
        """Загрузка чека для статьи расходов"""
        from app.models.spending_item import SpendingItem
        from app.models.grant import Grant
        from app.core.config import settings
        
        # Проверка существования статьи расходов
        result = await db.execute(
            select(SpendingItem).where(SpendingItem.id == spending_item_id)
        )
        spending_item = result.scalar_one_or_none()
        if not spending_item:
            raise ValueError("Spending item not found")
        
        # Проверка, что грант назначен на текущего grantee
        result = await db.execute(
            select(Grant).where(Grant.id == spending_item.grant_id)
        )
        grant = result.scalar_one_or_none()
        if not grant:
            raise ValueError("Grant not found")
        
        if grant.grantee_id != uploaded_by:
            raise ValueError("Grant is not assigned to you")
        
        # Валидация файла
        allowed_extensions = {'.png', '.jpg', '.jpeg', '.pdf'}
        file_ext = Path(filename).suffix.lower()
        if file_ext not in allowed_extensions:
            raise ValueError(f"Invalid file format. Allowed: {', '.join(allowed_extensions)}")
        
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise ValueError(f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024 * 1024)}MB")
        
        # Сохранение файла
        upload_dir = Path(settings.UPLOAD_DIR) / "spending_items"
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        file_name = f"{spending_item_id}_{uuid.uuid4()}{file_ext}"
        file_path = upload_dir / file_name
        
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Проверка существующего чека (можно заменить)
        result = await db.execute(
            select(Receipt).where(Receipt.spending_item_id == spending_item_id)
            .order_by(Receipt.created_at.desc())
        )
        existing_receipt = result.scalar_one_or_none()
        
        if existing_receipt:
            # Удаляем старый файл (опционально, можно оставить для аудита)
            # os.remove(existing_receipt.file_path)
            # Обновляем существующий чек
            existing_receipt.file_path = str(file_path)
            existing_receipt.verified = False
            existing_receipt.verified_at = None
            await db.commit()
            await db.refresh(existing_receipt)
            return existing_receipt
        
        # Создание новой записи
        receipt = Receipt(
            spending_item_id=spending_item_id,
            file_path=str(file_path),
            uploaded_by=uploaded_by,
            verified=False
        )
        db.add(receipt)
        await db.commit()
        await db.refresh(receipt)
        
        return receipt


receipt_service = ReceiptService()


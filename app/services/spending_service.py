"""
Сервис для работы с расходами
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.models.spending_item import SpendingItem
from app.models.spending_request import SpendingRequest
from app.models.grant import Grant
from app.models.receipt import Receipt
from app.schemas.spending import SpendingItemCreate, SpendingRequestCreate
from app.services.aml_engine import aml_engine
from app.services.smart_contract_service import smart_contract_service
from app.utils.enums import SpendingRequestStatus, UserRole
from app.core.config import settings
from decimal import Decimal


class SpendingService:
    """Сервис для управления расходами"""
    
    @staticmethod
    async def create_spending_items(
        db: AsyncSession,
        grant_id: int,
        items: list[SpendingItemCreate],
        grantee_id: int
    ) -> list[SpendingItem]:
        """Создание мета-пунктов расходов"""
        # Проверка прав
        result = await db.execute(select(Grant).where(Grant.id == grant_id))
        grant = result.scalar_one_or_none()
        if not grant:
            raise ValueError("Grant not found")
        
        # Создание items
        created_items = []
        for item_data in items:
            item = SpendingItem(
                grant_id=grant_id,
                title=item_data.title,
                planned_amount=item_data.planned_amount,
                priority_index=item_data.priority_index
            )
            db.add(item)
            created_items.append(item)
        
        await db.commit()
        for item in created_items:
            await db.refresh(item)
        
        return created_items
    
    @staticmethod
    async def create_spending_items_from_file(
        db: AsyncSession,
        grant_id: int,
        file_content: bytes,
        filename: str
    ) -> list[SpendingItem]:
        """Создание мета-пунктов расходов из Excel/CSV файла"""
        import pandas as pd
        import io
        from pathlib import Path
        
        # Проверка существования гранта
        result = await db.execute(select(Grant).where(Grant.id == grant_id))
        grant = result.scalar_one_or_none()
        if not grant:
            raise ValueError("Grant not found")
        
        # Определение формата файла
        file_ext = Path(filename).suffix.lower()
        
        try:
            # Парсинг файла
            if file_ext in ['.xlsx', '.xls']:
                df = pd.read_excel(io.BytesIO(file_content))
            elif file_ext == '.csv':
                df = pd.read_csv(io.BytesIO(file_content))
            else:
                raise ValueError(f"Unsupported file format. Allowed: .xlsx, .xls, .csv")
        except Exception as e:
            raise ValueError(f"Error parsing file: {str(e)}")
        
        # Нормализация названий колонок (регистронезависимо)
        df.columns = df.columns.str.strip()
        column_mapping = {}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower == 'title':
                column_mapping[col] = 'title'
            elif col_lower == 'amount':
                column_mapping[col] = 'amount'
            elif col_lower == 'description':
                column_mapping[col] = 'description'
        
        # Переименование колонок
        df = df.rename(columns=column_mapping)
        
        # Проверка наличия обязательных колонок (после нормализации)
        required_columns = ['title', 'amount']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise ValueError(f"Missing required columns: {', '.join([c.capitalize() for c in missing_columns])}")
        
        # Валидация и создание items
        created_items = []
        errors = []
        
        # Получаем текущий максимальный priority_index для гранта
        result = await db.execute(
            select(func.max(SpendingItem.priority_index))
            .where(SpendingItem.grant_id == grant_id)
        )
        max_priority = result.scalar_one_or_none() or 0
        
        for idx, row in df.iterrows():
            try:
                # Валидация title
                title = str(row.get('title', '')).strip()
                if not title:
                    errors.append(f"Row {idx + 2}: Title is required")
                    continue
                
                # Валидация amount
                amount = row.get('amount')
                if pd.isna(amount):
                    errors.append(f"Row {idx + 2}: Amount is required")
                    continue
                
                try:
                    amount_decimal = Decimal(str(amount))
                    if amount_decimal <= 0:
                        errors.append(f"Row {idx + 2}: Amount must be positive")
                        continue
                except (ValueError, TypeError):
                    errors.append(f"Row {idx + 2}: Invalid amount format")
                    continue
                
                # Создание item
                item = SpendingItem(
                    grant_id=grant_id,
                    title=title,
                    planned_amount=amount_decimal,
                    priority_index=max_priority + idx + 1
                )
                db.add(item)
                created_items.append(item)
                
            except Exception as e:
                errors.append(f"Row {idx + 2}: {str(e)}")
        
        if errors and not created_items:
            raise ValueError(f"File validation errors:\n" + "\n".join(errors))
        
        if created_items:
            await db.commit()
            for item in created_items:
                await db.refresh(item)
        
        if errors:
            # Если есть частично созданные items, все равно возвращаем их
            # но предупреждаем об ошибках
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Some rows had errors: {errors}")
        
        return created_items
    
    @staticmethod
    async def create_spending_request(
        db: AsyncSession,
        request_data: SpendingRequestCreate,
        grantee_id: int
    ) -> SpendingRequest:
        """Создание запроса на транш"""
        # Получаем spending_item
        result = await db.execute(
            select(SpendingItem).where(SpendingItem.id == request_data.spending_item_id)
        )
        spending_item = result.scalar_one_or_none()
        if not spending_item:
            raise ValueError("Spending item not found")
        
        # Получаем грант (используем grant_id из request_data если есть, иначе из spending_item)
        grant_id = getattr(request_data, 'grant_id', None) or spending_item.grant_id
        result = await db.execute(select(Grant).where(Grant.id == grant_id))
        grant = result.scalar_one_or_none()
        if not grant:
            raise ValueError("Grant not found")
        
        # Проверка: нельзя запросить новый транш, пока не загружен чек предыдущего
        result = await db.execute(
            select(SpendingRequest).where(
                and_(
                    SpendingRequest.grantee_id == grantee_id,
                    SpendingRequest.spending_item_id == request_data.spending_item_id,
                    SpendingRequest.status.in_([
                        SpendingRequestStatus.PAID.value,
                        SpendingRequestStatus.PENDING_RECEIPT.value
                    ])
                )
            ).order_by(SpendingRequest.created_at.desc())
        )
        last_request = result.scalar_one_or_none()
        if last_request:
            if last_request.status == SpendingRequestStatus.PAID.value:
                # Проверяем наличие чека
                receipt_result = await db.execute(
                    select(Receipt).where(Receipt.spending_request_id == last_request.id)
                )
                receipt = receipt_result.scalar_one_or_none()
                if not receipt or not receipt.verified:
                    raise ValueError("Cannot create new request: previous receipt not verified")
        
        # Проверка превышения бюджета
        if float(grant.amount_spent) + float(request_data.amount) > float(grant.total_amount):
            raise ValueError("Amount exceeds grant budget")
        
        # Определение статуса: топ-3 требуют одобрения
        status = SpendingRequestStatus.PENDING_UNIVERSITY_APPROVAL.value
        if settings.TOP_3_APPROVAL_REQUIRED:
            result = await db.execute(
                select(SpendingItem).where(SpendingItem.grant_id == grant.id)
                .order_by(SpendingItem.priority_index.asc())
                .limit(3)
            )
            top3_items = result.scalars().all()
            if spending_item.id not in [item.id for item in top3_items]:
                status = SpendingRequestStatus.PENDING_RECEIPT.value
        
        # Создание запроса
        request = SpendingRequest(
            spending_item_id=request_data.spending_item_id,
            grantee_id=grantee_id,
            amount=request_data.amount,
            status=status
        )
        
        # AML проверка
        from app.models.user import User
        result = await db.execute(select(User).where(User.id == grantee_id))
        grantee = result.scalar_one_or_none()
        aml_flags = await aml_engine.check_spending_request(db, request, grant, grantee)
        request.aml_flags = aml_flags
        
        # Если есть AML флаги, статус меняется на blocked
        if aml_flags:
            request.status = SpendingRequestStatus.BLOCKED.value
        
        db.add(request)
        await db.commit()
        await db.refresh(request)
        
        # Логирование в смарт-контракт
        await smart_contract_service.create_spending_request(
            db,
            request.id,
            request.spending_item_id,
            float(request.amount)
        )
        
        return request
    
    @staticmethod
    async def approve_request(
        db: AsyncSession,
        request_id: int,
        university_user_id: int,
        approved: bool,
        rejection_reason: str | None = None
    ) -> SpendingRequest:
        """Одобрение/отклонение запроса университетом"""
        result = await db.execute(
            select(SpendingRequest).where(SpendingRequest.id == request_id)
        )
        request = result.scalar_one_or_none()
        if not request:
            raise ValueError("Spending request not found")
        
        if request.status != SpendingRequestStatus.PENDING_UNIVERSITY_APPROVAL.value:
            raise ValueError("Request is not pending university approval")
        
        if approved:
            request.status = SpendingRequestStatus.PENDING_RECEIPT.value
            request.approved_by_university = university_user_id
            await smart_contract_service.approve_spending_request(db, request_id, university_user_id)
        else:
            request.status = SpendingRequestStatus.REJECTED.value
            request.rejection_reason = rejection_reason
            await smart_contract_service.reject_spending_request(db, request_id, rejection_reason or "Rejected")
        
        await db.commit()
        await db.refresh(request)
        return request


spending_service = SpendingService()


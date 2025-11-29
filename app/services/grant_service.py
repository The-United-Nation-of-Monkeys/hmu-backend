"""
Сервис для работы с грантами
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.grant import Grant
from app.models.user import User
from app.schemas.grant import GrantCreate
from app.services.smart_contract_service import smart_contract_service
from app.utils.enums import UserRole, GrantState
from decimal import Decimal


class GrantService:
    """Сервис для управления грантами"""
    
    @staticmethod
    async def create_grant(
        db: AsyncSession,
        grant_data: GrantCreate,
        created_by: int
    ) -> Grant:
        """Создание гранта"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Проверка, что пользователь - government
            result = await db.execute(select(User).where(User.id == created_by))
            user = result.scalar_one_or_none()
            if not user or user.role != UserRole.GOVERNMENT:
                raise ValueError("Only government users can create grants")
            
            # Проверка, что university существует
            result = await db.execute(select(User).where(User.id == grant_data.university_id))
            university = result.scalar_one_or_none()
            if not university or university.role != UserRole.UNIVERSITY:
                raise ValueError(f"Invalid university ID: {grant_data.university_id}")
            
            # Создание гранта
            grant = Grant(
                title=grant_data.title,
                total_amount=grant_data.total_amount,
                university_id=grant_data.university_id,
                state=GrantState.ACTIVE.value
            )
            db.add(grant)
            await db.commit()
            await db.refresh(grant)
            
            logger.info(f"Grant created: id={grant.id}, title={grant.title}, amount={grant.total_amount}")
            
            # Логирование в смарт-контракт
            try:
                await smart_contract_service.create_grant(
                    db,
                    grant.id,
                    float(grant.total_amount),
                    grant.university_id
                )
            except Exception as e:
                logger.error(f"Failed to log grant to smart contract: {e}")
                # Не прерываем создание гранта, если логирование не удалось
                # В production можно добавить retry или очередь
        
            return grant
        except Exception as e:
            logger.error(f"Error in create_grant: {e}")
            await db.rollback()
            raise
    
    @staticmethod
    async def get_grant(db: AsyncSession, grant_id: int) -> Grant | None:
        """Получение гранта по ID"""
        result = await db.execute(select(Grant).where(Grant.id == grant_id))
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_grants_by_university(
        db: AsyncSession,
        university_id: int
    ) -> list[Grant]:
        """Получение грантов университета"""
        result = await db.execute(
            select(Grant).where(Grant.university_id == university_id)
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_grants_by_grantee(
        db: AsyncSession,
        grantee_id: int
    ) -> list[Grant]:
        """Получение грантов грантополучателя (через spending_items)"""
        from app.models.spending_item import SpendingItem
        from app.models.spending_request import SpendingRequest
        
        # Получаем все гранты, где есть spending_items с запросами от этого grantee
        result = await db.execute(
            select(Grant).join(SpendingItem).join(SpendingRequest).where(
                SpendingRequest.grantee_id == grantee_id
            ).distinct()
        )
        return list(result.scalars().all())
    
    @staticmethod
    async def get_all_grants(db: AsyncSession) -> list[Grant]:
        """Получение всех грантов"""
        result = await db.execute(
            select(Grant).order_by(Grant.created_at.desc())
        )
        return list(result.scalars().all())


grant_service = GrantService()


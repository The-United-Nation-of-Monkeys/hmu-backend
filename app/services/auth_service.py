"""
Сервис аутентификации
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.core.security import verify_password, get_password_hash
from app.schemas.auth import UserSignup
from app.utils.enums import UserRole


class AuthService:
    """Сервис для работы с аутентификацией"""
    
    @staticmethod
    async def create_user(db: AsyncSession, user_data: UserSignup) -> User:
        """Создание пользователя"""
        # Проверка существующего пользователя
        result = await db.execute(select(User).where(User.email == user_data.email))
        existing_user = result.scalar_one_or_none()
        if existing_user:
            raise ValueError("User with this email already exists")
        
        # Создание пользователя
        user = User(
            email=user_data.email,
            password_hash=get_password_hash(user_data.password),
            name=user_data.name,
            role=UserRole(user_data.role)
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user
    
    @staticmethod
    async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
        """Аутентификация пользователя"""
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user
    
    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
        """Получение пользователя по ID"""
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


auth_service = AuthService()


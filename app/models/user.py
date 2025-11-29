"""
Модель пользователя
"""
from sqlalchemy import Column, Integer, String, Enum
from app.db import Base
import enum


class UserRole(str, enum.Enum):
    """Роли пользователей"""
    GRANTOR = "grantor"  # Грантодатель
    GRANTEE = "grantee"  # Грантополучатель


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    role = Column(Enum(UserRole), nullable=False, index=True)
    
    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', role='{self.role}')>"


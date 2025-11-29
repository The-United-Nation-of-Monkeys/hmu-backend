"""
Модель гранта
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class Grant(Base):
    """Модель гранта"""
    __tablename__ = "grants"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    amount_total = Column(Numeric(18, 2), nullable=False)  # Общая сумма гранта
    amount_spent = Column(Numeric(18, 2), default=0)  # Потраченная сумма
    grantee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    blockchain_address = Column(String, nullable=True, index=True)  # Адрес смарт-контракта
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    grantee = relationship("User", backref="grants")
    expenses = relationship("Expense", back_populates="grant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Grant(id={self.id}, title='{self.title}', amount_total={self.amount_total})>"


"""
Модель расхода
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, Enum, ARRAY, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db import Base
import enum


class ExpenseStatus(str, enum.Enum):
    """Статусы расхода"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MANUAL_REVIEW = "manual_review"


class Expense(Base):
    """Модель расхода"""
    __tablename__ = "expenses"
    
    id = Column(Integer, primary_key=True, index=True)
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=False, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id"), nullable=True, index=True)
    amount = Column(Numeric(18, 2), nullable=False, index=True)
    category = Column(String, nullable=True, index=True)
    status = Column(Enum(ExpenseStatus), nullable=False, default=ExpenseStatus.PENDING, index=True)
    aml_flags = Column(ARRAY(Text), default=[])  # Флаги AML проверки
    comment = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    grant = relationship("Grant", back_populates="expenses")
    transaction = relationship("Transaction", backref="expenses")
    
    def __repr__(self):
        return f"<Expense(id={self.id}, grant_id={self.grant_id}, amount={self.amount}, status='{self.status}')>"


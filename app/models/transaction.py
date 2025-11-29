"""
Модель транзакции
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Transaction(Base):
    """Модель транзакции"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    spending_request_id = Column(Integer, ForeignKey("spending_requests.id"), nullable=True, index=True)
    source = Column(String, nullable=False)
    destination = Column(String, nullable=False)
    amount = Column(Numeric(18, 2), nullable=False)
    currency = Column(String, default="RUB")
    external_id = Column(String, nullable=True, index=True)  # MIR transaction ID
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    spending_request = relationship("SpendingRequest", back_populates="transaction")
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, amount={self.amount}, external_id='{self.external_id}')>"


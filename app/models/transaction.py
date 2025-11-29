"""
Модель транзакции от МИР
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, JSON, Index
from sqlalchemy.sql import func
from app.db import Base


class Transaction(Base):
    """Модель транзакции от МИР"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    mir_id = Column(String, unique=True, nullable=False, index=True)  # ID транзакции от МИР
    amount = Column(Numeric(18, 2), nullable=False, index=True)
    mcc_code = Column(String, nullable=True, index=True)  # Merchant Category Code
    merchant_name = Column(String, nullable=True, index=True)
    has_receipt = Column(Boolean, default=False, index=True)
    raw_receipt_json = Column(JSON, nullable=True)  # Сырые данные чека
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Индекс для поиска дубликатов
    __table_args__ = (
        Index('idx_mir_id', 'mir_id'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Transaction(id={self.id}, mir_id='{self.mir_id}', amount={self.amount})>"


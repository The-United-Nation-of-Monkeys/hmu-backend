"""
Модель лога операций смарт-контракта
"""
from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from app.db.base import Base
from app.utils.enums import OperationType


class SmartContractOperationLog(Base):
    """Модель лога операций смарт-контракта"""
    __tablename__ = "smart_contract_operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    operation_type = Column(String, nullable=False, index=True)  # OperationType
    payload = Column(JSON, nullable=False)
    result = Column(Text, nullable=True)
    tx_hash = Column(String, nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    def __repr__(self):
        return f"<SmartContractOperationLog(id={self.id}, operation_type='{self.operation_type}', tx_hash='{self.tx_hash}')>"


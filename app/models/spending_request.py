"""
Модель запроса на транш
"""
from sqlalchemy import Column, Integer, Numeric, ForeignKey, DateTime, String, ARRAY, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.utils.enums import SpendingRequestStatus


# PostgreSQL enum для статуса запроса
spendingrequeststatus_enum = ENUM(
    'pending_university_approval', 'pending_receipt', 'paid', 'rejected', 'blocked',
    name='spendingrequeststatus',
    create_type=False
)


class SpendingRequest(Base):
    """Модель запроса на транш"""
    __tablename__ = "spending_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    spending_item_id = Column(Integer, ForeignKey("spending_items.id"), nullable=False, index=True)
    grantee_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    amount = Column(Numeric(18, 2), nullable=False)
    status = Column(spendingrequeststatus_enum, default='pending_university_approval', index=True)
    aml_flags = Column(ARRAY(Text), default=[])
    approved_by_university = Column(Integer, ForeignKey("users.id"), nullable=True)
    paid_tx_hash = Column(String, nullable=True, index=True)
    rejection_reason = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    spending_item = relationship("SpendingItem", back_populates="spending_requests")
    grantee = relationship("User", foreign_keys=[grantee_id], backref="spending_requests")
    approver = relationship("User", foreign_keys=[approved_by_university])
    receipt = relationship("Receipt", back_populates="spending_request", uselist=False, cascade="all, delete-orphan")
    transaction = relationship("Transaction", back_populates="spending_request", uselist=False)
    
    def __repr__(self):
        return f"<SpendingRequest(id={self.id}, amount={self.amount}, status='{self.status}')>"


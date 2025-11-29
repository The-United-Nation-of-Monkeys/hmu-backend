"""
Модель чека
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Receipt(Base):
    """Модель чека"""
    __tablename__ = "receipts"
    
    id = Column(Integer, primary_key=True, index=True)
    spending_request_id = Column(Integer, ForeignKey("spending_requests.id"), nullable=True, unique=True, index=True)
    spending_item_id = Column(Integer, ForeignKey("spending_items.id"), nullable=True, index=True)
    file_path = Column(String, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    verified = Column(Boolean, default=False, index=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    spending_request = relationship("SpendingRequest", back_populates="receipt")
    spending_item = relationship("SpendingItem", backref="receipts")
    uploader = relationship("User", foreign_keys=[uploaded_by])
    
    def __repr__(self):
        return f"<Receipt(id={self.id}, verified={self.verified})>"


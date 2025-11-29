"""
Модель гранта
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base
from app.utils.enums import GrantState


# PostgreSQL enum для состояния гранта
grantstate_enum = ENUM('active', 'completed', 'cancelled', name='grantstate', create_type=False)


class Grant(Base):
    """Модель гранта"""
    __tablename__ = "grants"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    total_amount = Column(Numeric(18, 2), nullable=False)
    amount_spent = Column(Numeric(18, 2), default=0)
    university_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    grantee_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    state = Column(grantstate_enum, default='active', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    university = relationship("User", foreign_keys=[university_id], backref="grants")
    grantee = relationship("User", foreign_keys=[grantee_id], backref="assigned_grants")
    spending_items = relationship("SpendingItem", back_populates="grant", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Grant(id={self.id}, title='{self.title}', total_amount={self.total_amount})>"


"""
Модель мета-пункта расходов
"""
from sqlalchemy import Column, Integer, String, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base import Base


class SpendingItem(Base):
    """Модель мета-пункта расходов"""
    __tablename__ = "spending_items"
    
    id = Column(Integer, primary_key=True, index=True)
    grant_id = Column(Integer, ForeignKey("grants.id"), nullable=False, index=True)
    title = Column(String, nullable=False)
    planned_amount = Column(Numeric(18, 2), nullable=False)
    priority_index = Column(Integer, nullable=False, index=True)  # Для определения топ-3
    
    # Relationships
    grant = relationship("Grant", back_populates="spending_items")
    spending_requests = relationship("SpendingRequest", back_populates="spending_item", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<SpendingItem(id={self.id}, title='{self.title}', planned_amount={self.planned_amount})>"


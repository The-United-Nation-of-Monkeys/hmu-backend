"""
Схемы для чеков
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import os


class ReceiptResponse(BaseModel):
    """Схема ответа с чеком"""
    id: int
    spending_request_id: int
    file_url: str
    uploaded_at: datetime
    verified: bool
    verified_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj):
        """Кастомная валидация для преобразования file_path в file_url"""
        filename = os.path.basename(obj.file_path) if obj.file_path else ""
        data = {
            "id": obj.id,
            "spending_request_id": obj.spending_request_id,
            "file_url": f"/api/files/{filename}" if filename else "",
            "uploaded_at": obj.created_at,
            "verified": obj.verified,
            "verified_at": obj.verified_at
        }
        return cls(**data)

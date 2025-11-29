"""
Схемы для смарт-контракта
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any


class SmartContractLogResponse(BaseModel):
    """Схема ответа с логом операции"""
    id: int
    transaction_hash: Optional[str] = None  # Изменено с tx_hash
    event_type: str  # Изменено с operation_type
    block_number: Optional[int] = None
    timestamp: datetime
    data: Dict[str, Any]  # Изменено с payload
    
    class Config:
        from_attributes = True
    
    @classmethod
    def model_validate(cls, obj):
        """Кастомная валидация для преобразования полей"""
        data = {
            "id": obj.id,
            "transaction_hash": obj.tx_hash,
            "event_type": obj.operation_type,
            "block_number": None,  # Можно добавить в модель позже
            "timestamp": obj.timestamp,
            "data": obj.payload if isinstance(obj.payload, dict) else {}
        }
        return cls(**data)


"""
Перечисления
"""
from enum import Enum


class UserRole(str, Enum):
    """Роли пользователей"""
    GOVERNMENT = "government"
    UNIVERSITY = "university"
    GRANTEE = "grantee"


class GrantState(str, Enum):
    """Состояния гранта"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class SpendingRequestStatus(str, Enum):
    """Статусы запроса на транш"""
    PENDING_UNIVERSITY_APPROVAL = "pending_university_approval"
    PENDING_RECEIPT = "pending_receipt"
    PAID = "paid"
    REJECTED = "rejected"
    BLOCKED = "blocked"


class OperationType(str, Enum):
    """Типы операций в смарт-контракте"""
    GRANT_CREATED = "grant_created"
    SPENDING_REQUEST_CREATED = "spending_request_created"
    SPENDING_REQUEST_APPROVED = "spending_request_approved"
    SPENDING_REQUEST_REJECTED = "spending_request_rejected"
    PAYMENT_EXECUTED = "payment_executed"
    RECEIPT_VERIFIED = "receipt_verified"


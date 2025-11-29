"""
AML (Anti-Money Laundering) движок
"""
from typing import List, Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from app.models.expense import Expense
from app.models.transaction import Transaction
from app.models.grant import Grant
from app.models.user import User
from app.config import settings
import re
from datetime import datetime, timedelta


class AMLEngine:
    """Движок для AML проверок"""
    
    @staticmethod
    def check(
        transaction: Optional[Transaction],
        expense: Expense,
        user: Optional[User],
        grant: Grant
    ) -> List[str]:
        """
        Проверка транзакции/расхода на AML нарушения
        
        Args:
            transaction: Транзакция от МИР
            expense: Расход
            user: Пользователь (грантополучатель)
            grant: Грант
            
        Returns:
            Список флагов AML
        """
        flags = []
        
        # 1. Проверка большой суммы (>20% от гранта)
        if grant.amount_total > 0:
            threshold = float(grant.amount_total) * settings.AML_LARGE_AMOUNT_THRESHOLD
            if float(expense.amount) > threshold:
                flags.append("large_amount")
        
        # 2. Проверка наличия чека
        if transaction:
            if not transaction.has_receipt:
                flags.append("no_receipt")
        
        # 3. Проверка подозрительного продавца (похож на ФИО)
        if transaction and transaction.merchant_name:
            if AMLEngine._is_person_name(transaction.merchant_name):
                flags.append("suspicious_merchant")
        
        # 4. Проверка аффилированности
        if transaction and transaction.merchant_name and user:
            if AMLEngine._is_affiliated(transaction.merchant_name, user.name):
                flags.append("affiliated_person")
        
        # 5. Проверка дубликатов (требует доступа к БД)
        # Эта проверка будет выполнена в expense_service
        
        return flags
    
    @staticmethod
    def _is_person_name(merchant_name: str) -> bool:
        """
        Проверка, похоже ли название продавца на ФИО
        
        Простая эвристика: если содержит слова, похожие на имена/фамилии
        """
        if not merchant_name:
            return False
        
        # Паттерны для определения ФИО
        # ООО/ИП обычно не содержат ФИО в названии
        org_prefixes = ["ООО", "ОАО", "ЗАО", "ИП", "ПАО", "АО", "LLC", "INC"]
        name_upper = merchant_name.upper()
        
        # Если начинается с организационной формы, скорее всего не ФИО
        for prefix in org_prefixes:
            if name_upper.startswith(prefix):
                return False
        
        # Простая проверка: если название короткое и содержит пробелы
        # и не содержит типичных слов для компаний
        words = merchant_name.split()
        if len(words) >= 2 and len(words) <= 4:
            # Проверяем, нет ли типичных слов компаний
            company_words = ["компания", "групп", "систем", "техно", "сервис", "центр"]
            has_company_word = any(word.lower() in merchant_name.lower() for word in company_words)
            if not has_company_word:
                return True
        
        return False
    
    @staticmethod
    def _is_affiliated(merchant_name: str, user_name: str) -> bool:
        """
        Проверка, является ли продавец аффилированным лицом
        (содержит имя/фамилию грантополучателя)
        """
        if not merchant_name or not user_name:
            return False
        
        merchant_lower = merchant_name.lower()
        user_lower = user_name.lower()
        
        # Извлекаем слова из имени пользователя
        user_words = user_lower.split()
        
        # Проверяем, содержит ли название продавца слова из имени пользователя
        for word in user_words:
            if len(word) > 3 and word in merchant_lower:  # Минимальная длина 3 символа
                return True
        
        return False
    
    @staticmethod
    def check_duplicates(
        db: Session,
        grant_id: int,
        amount: Decimal,
        transaction_id: Optional[int] = None,
        window_minutes: int = None
    ) -> bool:
        """
        Проверка на дублирующиеся транзакции
        
        Args:
            db: Сессия БД
            grant_id: ID гранта
            amount: Сумма
            transaction_id: ID текущей транзакции (для исключения)
            window_minutes: Окно времени для проверки
            
        Returns:
            True если найдены дубликаты
        """
        if window_minutes is None:
            window_minutes = settings.AML_DUPLICATE_WINDOW_MINUTES
        
        # Время окна
        time_threshold = datetime.utcnow() - timedelta(minutes=window_minutes)
        
        # Ищем расходы с такой же суммой в этом окне
        query = db.query(Expense).filter(
            Expense.grant_id == grant_id,
            Expense.amount == amount,
            Expense.created_at >= time_threshold
        )
        
        if transaction_id:
            # Исключаем текущую транзакцию
            query = query.join(Transaction).filter(Transaction.id != transaction_id)
        
        duplicates = query.count()
        return duplicates > 0


# Глобальный экземпляр движка
aml_engine = AMLEngine()


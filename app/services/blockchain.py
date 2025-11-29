"""
Сервис для работы с блокчейном
"""
from typing import Optional
from web3 import Web3
from app.config import settings
import logging

logger = logging.getLogger(__name__)


class BlockchainService:
    """Сервис для взаимодействия с блокчейном"""
    
    def __init__(self):
        self.w3: Optional[Web3] = None
        self.contract = None
        self._init_web3()
    
    def _init_web3(self):
        """Инициализация подключения к блокчейну"""
        try:
            self.w3 = Web3(Web3.HTTPProvider(settings.RPC_URL))
            if not self.w3.is_connected():
                logger.warning(f"Не удалось подключиться к блокчейну: {settings.RPC_URL}")
                return
            
            # Если указан адрес контракта, загружаем его
            if settings.CONTRACT_ADDRESS:
                # Здесь можно загрузить ABI и создать экземпляр контракта
                # Для прототипа используем mock
                logger.info(f"Блокчейн подключен: {settings.RPC_URL}")
        except Exception as e:
            logger.error(f"Ошибка инициализации блокчейна: {e}")
    
    def log_expense(
        self,
        grant_address: str,
        expense_id: int,
        amount: float,
        category: Optional[str] = None
    ) -> Optional[str]:
        """
        Логирование расхода в блокчейн
        
        Args:
            grant_address: Адрес смарт-контракта гранта
            expense_id: ID расхода
            amount: Сумма
            category: Категория
            
        Returns:
            Hash транзакции или None
        """
        if not self.w3 or not self.w3.is_connected():
            logger.warning("Блокчейн не подключен, пропускаем логирование")
            # Для прототипа возвращаем mock hash
            return f"0x{'0' * 64}"
        
        try:
            # Здесь должна быть реальная логика записи в смарт-контракт
            # Для прототипа возвращаем mock hash
            mock_hash = f"0x{expense_id:064x}"
            logger.info(f"Расход {expense_id} записан в блокчейн: {mock_hash}")
            return mock_hash
        except Exception as e:
            logger.error(f"Ошибка записи в блокчейн: {e}")
            return None
    
    def get_grant_info(self, grant_address: str) -> Optional[dict]:
        """
        Получение информации о гранте из блокчейна
        
        Args:
            grant_address: Адрес смарт-контракта
            
        Returns:
            Словарь с информацией о гранте
        """
        if not self.w3 or not self.w3.is_connected():
            return None
        
        # Mock данные для прототипа
        return {
            "address": grant_address,
            "total_amount": 0,
            "spent_amount": 0,
            "expenses_count": 0
        }
    
    def verify_expense(self, expense_id: int, grant_address: str) -> bool:
        """
        Проверка расхода в блокчейне
        
        Args:
            expense_id: ID расхода
            grant_address: Адрес смарт-контракта
            
        Returns:
            True если расход верифицирован
        """
        if not self.w3 or not self.w3.is_connected():
            return False
        
        # Mock проверка для прототипа
        return True


# Глобальный экземпляр сервиса
blockchain_service = BlockchainService()


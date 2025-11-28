"""
Модуль для управления грантами через смарт-контракт
"""
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
from typing import Optional, Dict, Any
from datetime import datetime
from src.deployer import ContractDeployer


load_dotenv()


class GrantManagerClient:
    """Клиент для работы с контрактом GrantManager"""
    
    GRANT_STATUS = {
        0: "Pending",
        1: "Approved",
        2: "Active",
        3: "Completed",
        4: "Cancelled"
    }
    
    def __init__(self, contract_address: str, rpc_url: Optional[str] = None, 
                 private_key: Optional[str] = None):
        """
        Инициализация клиента
        
        Args:
            contract_address: Адрес развернутого контракта
            rpc_url: URL RPC узла Ethereum
            private_key: Приватный ключ для подписи транзакций
        """
        self.contract_address = contract_address
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://localhost:8545")
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        
        if not self.private_key:
            raise ValueError("Private key is required")
        
        # Подключение к сети
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        try:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except:
            pass
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Ethereum node at {self.rpc_url}")
        
        # Настройка аккаунта
        self.account = Account.from_key(self.private_key)
        self.w3.eth.default_account = self.account.address
        
        # Получение экземпляра контракта
        deployer = ContractDeployer(self.rpc_url, self.private_key)
        self.contract = deployer.get_contract_instance(contract_address, "GrantManager")
    
    def create_grant(
        self,
        recipient: str,
        amount: float,
        description: str,
        deadline: int,
        requires_approval: bool = True
    ) -> Dict[str, Any]:
        """
        Создание нового гранта
        
        Args:
            recipient: Адрес получателя
            amount: Сумма гранта в ETH
            description: Описание гранта
            deadline: Срок выполнения (Unix timestamp)
            requires_approval: Требуется ли одобрение
            
        Returns:
            Результат создания гранта
        """
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        transaction = self.contract.functions.createGrant(
            recipient,
            amount_wei,
            description,
            deadline,
            requires_approval
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 500000,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Получение ID гранта из события
        grant_id = None
        if tx_receipt.status == 1:
            logs = self.contract.events.GrantCreated().process_receipt(tx_receipt)
            if logs:
                grant_id = logs[0]['args']['grantId']
        
        return {
            'grant_id': grant_id,
            'tx_hash': tx_hash.hex(),
            'status': 'success' if tx_receipt.status == 1 else 'failed'
        }
    
    def approve_grant(self, grant_id: int) -> Dict[str, Any]:
        """
        Одобрение гранта
        
        Args:
            grant_id: ID гранта
            
        Returns:
            Результат одобрения
        """
        transaction = self.contract.functions.approveGrant(grant_id).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 200000,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'status': 'success' if tx_receipt.status == 1 else 'failed'
        }
    
    def allocate_funds(self, grant_id: int, amount: float) -> Dict[str, Any]:
        """
        Выделение средств для гранта
        
        Args:
            grant_id: ID гранта
            amount: Сумма для выделения в ETH
            
        Returns:
            Результат выделения средств
        """
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        transaction = self.contract.functions.allocateFunds(
            grant_id,
            amount_wei
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'status': 'success' if tx_receipt.status == 1 else 'failed'
        }
    
    def release_funds(self, grant_id: int, amount: float) -> Dict[str, Any]:
        """
        Выпуск средств получателю
        
        Args:
            grant_id: ID гранта
            amount: Сумма для выпуска в ETH
            
        Returns:
            Результат выпуска средств
        """
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        transaction = self.contract.functions.releaseFunds(
            grant_id,
            amount_wei
        ).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': 300000,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'status': 'success' if tx_receipt.status == 1 else 'failed'
        }
    
    def get_grant(self, grant_id: int) -> Dict[str, Any]:
        """
        Получение информации о гранте
        
        Args:
            grant_id: ID гранта
            
        Returns:
            Информация о гранте
        """
        grant_data = self.contract.functions.getGrant(grant_id).call()
        
        return {
            'id': grant_data[0],
            'recipient': grant_data[1],
            'amount': self.w3.from_wei(grant_data[2], 'ether'),
            'allocated_amount': self.w3.from_wei(grant_data[3], 'ether'),
            'released_amount': self.w3.from_wei(grant_data[4], 'ether'),
            'description': grant_data[5],
            'status': self.GRANT_STATUS[grant_data[6]],
            'created_at': datetime.fromtimestamp(grant_data[7]),
            'deadline': datetime.fromtimestamp(grant_data[8]),
            'requires_approval': grant_data[9],
            'approval_count': grant_data[10]
        }
    
    def get_contract_balance(self) -> float:
        """
        Получение баланса контракта
        
        Returns:
            Баланс в ETH
        """
        balance_wei = self.contract.functions.getBalance().call()
        return float(self.w3.from_wei(balance_wei, 'ether'))
    
    def deposit(self, amount: float) -> Dict[str, Any]:
        """
        Пополнение контракта средствами
        
        Args:
            amount: Сумма для пополнения в ETH
            
        Returns:
            Результат пополнения
        """
        amount_wei = self.w3.to_wei(amount, 'ether')
        
        transaction = self.contract.functions.deposit().build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'value': amount_wei,
            'gas': 100000,
        })
        
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        return {
            'tx_hash': tx_hash.hex(),
            'status': 'success' if tx_receipt.status == 1 else 'failed'
        }
    
    def get_grant_count(self) -> int:
        """
        Получение количества грантов
        
        Returns:
            Количество грантов
        """
        return self.contract.functions.grantCount().call()
    
    def list_grants(self, limit: int = 10) -> list:
        """
        Получение списка грантов
        
        Args:
            limit: Максимальное количество грантов
            
        Returns:
            Список грантов
        """
        grant_count = self.get_grant_count()
        grants = []
        
        for i in range(1, min(grant_count + 1, limit + 1)):
            try:
                grant = self.get_grant(i)
                grants.append(grant)
            except Exception as e:
                print(f"Error fetching grant {i}: {e}")
        
        return grants


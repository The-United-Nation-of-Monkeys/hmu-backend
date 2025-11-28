"""
Модуль для развертывания смарт-контрактов
"""
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account
from dotenv import load_dotenv
from typing import Optional
from src.compiler import ContractCompiler


load_dotenv()


class ContractDeployer:
    """Класс для развертывания смарт-контрактов"""
    
    def __init__(self, rpc_url: Optional[str] = None, private_key: Optional[str] = None):
        """
        Инициализация деплоера
        
        Args:
            rpc_url: URL RPC узла Ethereum
            private_key: Приватный ключ для подписи транзакций
        """
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "http://localhost:8545")
        self.private_key = private_key or os.getenv("PRIVATE_KEY")
        
        if not self.private_key:
            raise ValueError("Private key is required. Set PRIVATE_KEY in .env or pass as parameter")
        
        # Подключение к сети
        self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
        
        # Для PoA сетей (например, BSC, Polygon)
        try:
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        except:
            pass
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to Ethereum node at {self.rpc_url}")
        
        # Настройка аккаунта
        self.account = Account.from_key(self.private_key)
        self.w3.eth.default_account = self.account.address
        
        print(f"✓ Connected to network: {self.rpc_url}")
        print(f"✓ Deployer address: {self.account.address}")
        print(f"✓ Balance: {self.w3.from_wei(self.w3.eth.get_balance(self.account.address), 'ether')} ETH")
        
        self.compiler = ContractCompiler()
    
    def deploy_contract(
        self, 
        contract_name: str, 
        constructor_args: tuple = (),
        gas_limit: Optional[int] = None,
        gas_price: Optional[int] = None
    ) -> dict:
        """
        Развертывание контракта
        
        Args:
            contract_name: Имя контракта для развертывания
            constructor_args: Аргументы конструктора
            gas_limit: Лимит газа
            gas_price: Цена газа
            
        Returns:
            Словарь с адресом контракта и транзакцией
        """
        # Компиляция контракта
        contract_interface = self.compiler.get_compiled_contract(contract_name)
        
        # Создание экземпляра контракта
        contract = self.w3.eth.contract(
            abi=contract_interface['abi'],
            bytecode=contract_interface['bin']
        )
        
        # Построение транзакции
        transaction = contract.constructor(*constructor_args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
            'gas': gas_limit or int(os.getenv("GAS_LIMIT", "3000000")),
            'gasPrice': gas_price or int(os.getenv("GAS_PRICE", "20000000000")),
        })
        
        # Подпись транзакции
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        
        # Отправка транзакции
        print(f"Deploying {contract_name}...")
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        
        # Ожидание подтверждения
        print(f"Transaction sent: {tx_hash.hex()}")
        print("Waiting for confirmation...")
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status != 1:
            raise Exception(f"Transaction failed: {tx_receipt}")
        
        contract_address = tx_receipt.contractAddress
        
        print(f"✓ Contract deployed successfully!")
        print(f"  Address: {contract_address}")
        print(f"  Transaction: {tx_hash.hex()}")
        print(f"  Gas used: {tx_receipt.gasUsed}")
        
        return {
            'address': contract_address,
            'tx_hash': tx_hash.hex(),
            'tx_receipt': tx_receipt,
            'abi': contract_interface['abi']
        }
    
    def get_contract_instance(self, contract_address: str, contract_name: str):
        """
        Получение экземпляра развернутого контракта
        
        Args:
            contract_address: Адрес контракта
            contract_name: Имя контракта
            
        Returns:
            Экземпляр контракта Web3
        """
        contract_interface = self.compiler.get_compiled_contract(contract_name)
        
        return self.w3.eth.contract(
            address=contract_address,
            abi=contract_interface['abi']
        )
    
    def deploy_grant_manager(self, min_approvals: int = 1) -> dict:
        """
        Развертывание контракта GrantManager
        
        Args:
            min_approvals: Минимальное количество одобрений
            
        Returns:
            Результат развертывания
        """
        return self.deploy_contract("GrantManager", constructor_args=(min_approvals,))


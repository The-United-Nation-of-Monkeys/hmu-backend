"""
Модуль для компиляции Solidity контрактов
"""
import json
import os
import subprocess
from pathlib import Path
from solcx import compile_source, install_solc, set_solc_version, get_installed_solc_versions


class ContractCompiler:
    """Класс для компиляции Solidity контрактов"""
    
    SOLIDITY_VERSION = "0.8.19"
    
    def __init__(self, contracts_dir: str = "contracts", output_dir: str = "contracts/compiled", 
                 skip_install: bool = False):
        """
        Инициализация компилятора
        
        Args:
            contracts_dir: Директория с Solidity контрактами
            output_dir: Директория для скомпилированных контрактов
            skip_install: Пропустить автоматическую установку solc
        """
        self.contracts_dir = Path(contracts_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.skip_install = skip_install
        self._setup_solc()
    
    def _check_system_solc(self):
        """Проверка наличия системного solc"""
        try:
            result = subprocess.run(
                ['solc', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                # Ищем строку с "Version:" во всем выводе
                for line in result.stdout.split('\n'):
                    if 'Version:' in line:
                        version = line.split('Version:')[1].strip().split('+')[0]
                        return version
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
            # Игнорируем ошибки при проверке системного solc
            pass
        return None
    
    def _setup_solc(self):
        """Установка и настройка Solidity компилятора"""
        # Сначала проверяем системный solc
        system_version = self._check_system_solc()
        if system_version:
            print(f"✓ Found system solc version: {system_version}")
            # Используем системную версию
            self.SOLIDITY_VERSION = system_version
            # Пытаемся установить эту версию для py-solc-x (если она еще не установлена)
            try:
                installed_versions = get_installed_solc_versions()
                if system_version not in installed_versions:
                    # Пытаемся установить системную версию через py-solc-x
                    # Но если это не получается, просто используем системный solc напрямую
                    print(f"Using system solc {system_version} (will compile without version specification)")
                else:
                    set_solc_version(system_version)
                    print(f"✓ Using system solc version: {system_version}")
            except:
                # Если не получается установить через py-solc-x, просто используем системный
                print(f"Using system solc {system_version} (will compile without version specification)")
            return
        
        # Если системного solc нет, работаем с py-solc-x
        try:
            # Проверяем, установлена ли уже нужная версия через py-solc-x
            installed_versions = get_installed_solc_versions()
            if self.SOLIDITY_VERSION in installed_versions:
                print(f"✓ Solidity {self.SOLIDITY_VERSION} already installed")
                set_solc_version(self.SOLIDITY_VERSION)
                return
            
            # Если есть другие установленные версии, используем их
            if installed_versions:
                latest_version = max(installed_versions)
                print(f"✓ Using installed version: {latest_version}")
                set_solc_version(latest_version)
                self.SOLIDITY_VERSION = str(latest_version)
                return
            
            # Если пропустить установку, выдаем ошибку
            if self.skip_install:
                raise Exception(
                    f"Solidity compiler {self.SOLIDITY_VERSION} not found. "
                    "Please install it manually or run without --skip-install flag."
                )
            
            # Пытаемся установить компилятор (может зависнуть!)
            print(f"⚠ Installing Solidity compiler {self.SOLIDITY_VERSION}...")
            print("⚠ This may take a long time or hang. If it does, press Ctrl+C and:")
            print("   1. Install solc manually: brew install solidity (macOS) or apt-get install solc (Linux)")
            print("   2. Or run: python -c \"from solcx import install_solc; install_solc('0.8.19')\" in background")
            print("   3. Or use --skip-install flag and install manually")
            
            try:
                install_solc(self.SOLIDITY_VERSION)
                set_solc_version(self.SOLIDITY_VERSION)
                print(f"✓ Solidity {self.SOLIDITY_VERSION} installed successfully")
            except KeyboardInterrupt:
                print("\n✗ Installation cancelled. Please install solc manually.")
                raise Exception(
                    "Solidity compiler installation was cancelled. "
                    "Please install manually or try again."
                )
        except Exception as e:
            if "KeyboardInterrupt" in str(type(e)):
                raise
            print(f"⚠ Warning: {e}")
            # Последняя попытка - использовать любую доступную версию
            try:
                installed_versions = get_installed_solc_versions()
                if installed_versions:
                    latest_version = max(installed_versions)
                    print(f"Using available version: {latest_version}")
                    set_solc_version(latest_version)
                    self.SOLIDITY_VERSION = str(latest_version)
                else:
                    raise Exception(
                        "No Solidity compiler found. "
                        "Please install manually:\n"
                        "  macOS: brew install solidity\n"
                        "  Linux: sudo apt-get install solc\n"
                        "  Or: python -c \"from solcx import install_solc; install_solc('0.8.19')\""
                    )
            except Exception as e2:
                print(f"✗ Error: {e2}")
                raise
    
    def compile_contract(self, contract_name: str) -> dict:
        """
        Компиляция контракта
        
        Args:
            contract_name: Имя контракта (без расширения .sol)
            
        Returns:
            Словарь с результатами компиляции
        """
        contract_path = self.contracts_dir / f"{contract_name}.sol"
        
        if not contract_path.exists():
            raise FileNotFoundError(f"Contract file not found: {contract_path}")
        
        print(f"Reading contract: {contract_path}")
        with open(contract_path, 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Компиляция
        print(f"Compiling {contract_name} with Solidity {self.SOLIDITY_VERSION}...")
        try:
            # Сначала пробуем без указания версии (использует системный solc, если доступен)
            compiled_sol = compile_source(
                source_code,
                output_values=['abi', 'bin']
            )
        except Exception as e:
            # Если не получилось без версии, пробуем с указанной версией
            try:
                print(f"Retrying compilation with version {self.SOLIDITY_VERSION}...")
                compiled_sol = compile_source(
                    source_code,
                    output_values=['abi', 'bin'],
                    solc_version=self.SOLIDITY_VERSION
                )
            except Exception as e2:
                raise Exception(f"Compilation failed. Tried without version: {e}. With version {self.SOLIDITY_VERSION}: {e2}")
        
        # Получение скомпилированного контракта
        contract_key = f"<stdin>:{contract_name}"
        if contract_key not in compiled_sol:
            # Попробуем найти контракт в других ключах
            available_keys = list(compiled_sol.keys())
            if not available_keys:
                raise Exception("No contracts found in compiled output")
            contract_key = available_keys[0]
            # Извлекаем имя контракта из ключа
            if ':' in contract_key:
                contract_name = contract_key.split(':')[1]
        
        contract_interface = compiled_sol[contract_key]
        
        # Сохранение результатов
        output_file = self.output_dir / f"{contract_name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(contract_interface, f, indent=2)
        
        print(f"✓ Contract compiled successfully: {contract_name}")
        print(f"  ABI saved to: {output_file}")
        
        return contract_interface
    
    def get_compiled_contract(self, contract_name: str) -> dict:
        """
        Загрузка скомпилированного контракта
        
        Args:
            contract_name: Имя контракта
            
        Returns:
            Словарь с ABI и bytecode
        """
        compiled_file = self.output_dir / f"{contract_name}.json"
        
        if not compiled_file.exists():
            raise FileNotFoundError(
                f"Compiled contract not found: {compiled_file}. "
                f"Please compile the contract first."
            )
        
        with open(compiled_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def compile_all(self) -> dict:
        """
        Компиляция всех контрактов в директории
        
        Returns:
            Словарь со всеми скомпилированными контрактами
        """
        compiled_contracts = {}
        
        for contract_file in self.contracts_dir.glob("*.sol"):
            contract_name = contract_file.stem
            try:
                compiled_contracts[contract_name] = self.compile_contract(contract_name)
            except Exception as e:
                print(f"✗ Error compiling {contract_name}: {e}")
        
        return compiled_contracts


#!/usr/bin/env python3
"""
Скрипт для установки Solidity компилятора
Можно запустить в фоновом режиме, если основная установка зависает
"""
import sys
from solcx import install_solc, set_solc_version, get_installed_solc_versions

VERSION = "0.8.19"

def main():
    print(f"Installing Solidity compiler {VERSION}...")
    print("This may take several minutes...")
    
    try:
        # Проверяем, не установлен ли уже
        installed = get_installed_solc_versions()
        if VERSION in installed:
            print(f"✓ Solidity {VERSION} is already installed")
            set_solc_version(VERSION)
            return 0
        
        # Устанавливаем
        install_solc(VERSION)
        set_solc_version(VERSION)
        print(f"✓ Solidity {VERSION} installed successfully!")
        return 0
    except KeyboardInterrupt:
        print("\n✗ Installation cancelled")
        return 1
    except Exception as e:
        print(f"✗ Error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())


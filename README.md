# Инструмент для управления грантовыми средствами через смарт-контракты

Программный инструмент на Python для создания и управления смарт-контрактами для эффективного управления грантовыми средствами на блокчейне Ethereum.

## Возможности

- ✅ Компиляция Solidity контрактов
- ✅ Развертывание контрактов в сеть Ethereum
- ✅ Создание и управление грантами
- ✅ Система одобрения грантов (мультиподпись)
- ✅ Выделение и выпуск средств
- ✅ Отслеживание статусов грантов
- ✅ CLI интерфейс для удобной работы

## Структура проекта

```
backend/
├── contracts/
│   ├── GrantManager.sol          # Смарт-контракт для управления грантами
│   └── compiled/                  # Скомпилированные контракты
├── src/
│   ├── __init__.py
│   ├── compiler.py                # Модуль компиляции контрактов
│   ├── deployer.py                # Модуль развертывания контрактов
│   └── grant_manager.py           # Клиент для работы с грантами
├── cli.py                         # CLI интерфейс
├── requirements.txt               # Зависимости Python
├── .gitignore
└── README.md
```

## Установка

1. Клонируйте репозиторий или скопируйте файлы проекта

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

3. Установите Solidity компилятор:

**Важно:** Автоматическая установка через `py-solc-x` может зависать. Рекомендуется установить solc вручную:

**macOS:**
```bash
brew install solidity
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install solc
```

**Альтернатива - установка через Python (может зависнуть):**
```bash
# В отдельном терминале или фоновом режиме:
python install_solc.py
# Или:
python -c "from solcx import install_solc; install_solc('0.8.19')"
```

**Если установка зависает:**
- Прервите процесс (Ctrl+C)
- Установите solc системно (см. выше)
- Используйте флаг `--skip-install` при компиляции:
  ```bash
  python cli.py compile --skip-install
  ```

4. Создайте файл `.env` с настройками:
```env
RPC_URL=http://localhost:8545
# Или для тестовой сети:
# RPC_URL=https://sepolia.infura.io/v3/YOUR_INFURA_KEY

PRIVATE_KEY=your_private_key_here
DEPLOYER_ADDRESS=your_deployer_address_here

GAS_LIMIT=3000000
GAS_PRICE=20000000000
```

## Использование

### Компиляция контрактов

```bash
python cli.py compile
# Или для конкретного контракта:
python cli.py compile --contract GrantManager
# Или все контракты:
python cli.py compile --all
# Пропустить автоматическую установку solc (если установлен системно):
python cli.py compile --skip-install
```

### Развертывание контракта

```bash
python cli.py deploy --min-approvals 2
```

Адрес развернутого контракта будет сохранен в `contract_config.json`.

### Управление грантами

#### Пополнение контракта средствами
```bash
python cli.py deposit --amount 10.0
```

#### Создание гранта
```bash
python cli.py create-grant \
  --recipient 0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb \
  --amount 5.0 \
  --description "Research grant for blockchain project" \
  --days 90
```

#### Одобрение гранта
```bash
python cli.py approve --grant-id 1
```

#### Выделение средств
```bash
python cli.py allocate --grant-id 1 --amount 5.0
```

#### Выпуск средств получателю
```bash
python cli.py release --grant-id 1 --amount 2.5
```

#### Просмотр информации о гранте
```bash
python cli.py info --grant-id 1
```

#### Список всех грантов
```bash
python cli.py list --limit 10
```

#### Просмотр баланса контракта
```bash
python cli.py balance
```

## Использование в Python коде

```python
from src.grant_manager import GrantManagerClient
from src.deployer import ContractDeployer

# Развертывание контракта
deployer = ContractDeployer()
result = deployer.deploy_grant_manager(min_approvals=2)
contract_address = result['address']

# Работа с грантами
client = GrantManagerClient(contract_address)

# Создание гранта
from datetime import datetime, timedelta
deadline = int((datetime.now() + timedelta(days=90)).timestamp())
result = client.create_grant(
    recipient="0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    amount=5.0,
    description="Research grant",
    deadline=deadline,
    requires_approval=True
)

# Получение информации о гранте
grant = client.get_grant(grant_id=1)
print(f"Grant status: {grant['status']}")
print(f"Amount: {grant['amount']} ETH")
```

## Функционал смарт-контракта

### Основные функции:

1. **Создание гранта** - создание нового гранта с указанием получателя, суммы и описания
2. **Одобрение гранта** - система мультиподписи для одобрения грантов
3. **Выделение средств** - выделение средств из баланса контракта для гранта
4. **Выпуск средств** - перевод средств получателю гранта
5. **Отмена гранта** - отмена гранта до начала выделения средств

### Статусы грантов:

- `Pending` - ожидает одобрения
- `Approved` - одобрен
- `Active` - активен (средства выделены)
- `Completed` - завершен (все средства выпущены)
- `Cancelled` - отменен

### Безопасность:

- Только владелец может создавать гранты и управлять средствами
- Система мультиподписи для одобрения грантов
- Контроль выделенных и выпущенных средств
- Защита от перерасхода средств

## Тестирование

Для тестирования рекомендуется использовать локальную сеть (Ganache) или тестовую сеть (Sepolia, Goerli).

### Использование Ganache:

1. Установите Ganache: https://trufflesuite.com/ganache/
2. Запустите локальную сеть
3. Обновите `RPC_URL` в `.env` на `http://localhost:8545`
4. Используйте приватные ключи из Ganache

## Требования

- Python 3.8+
- Node.js (для Solidity компилятора)
- Доступ к Ethereum RPC узлу (локальный или через Infura/Alchemy)

## Лицензия

MIT

## Поддержка

При возникновении проблем проверьте:
- Правильность настроек в `.env`
- Доступность RPC узла
- Достаточность баланса для транзакций
- Правильность адресов получателей


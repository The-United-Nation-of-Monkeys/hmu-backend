# SmartGrant Backend API

Backend платформы SmartGrant для управления грантовыми средствами с интеграцией МИР, AML-проверками и блокчейном.

## Технологии

- **Python 3.11+**
- **FastAPI** - современный веб-фреймворк
- **SQLAlchemy 2.0** - ORM
- **PostgreSQL** - база данных
- **Web3.py** - работа с блокчейном
- **Pydantic** - валидация данных

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── config.py            # Конфигурация
│   ├── db.py                # Настройка БД
│   ├── models/              # SQLAlchemy модели
│   │   ├── user.py
│   │   ├── grant.py
│   │   ├── transaction.py
│   │   └── expense.py
│   ├── schemas/             # Pydantic схемы
│   │   ├── grant.py
│   │   ├── transaction.py
│   │   ├── expense.py
│   │   └── aml.py
│   ├── routers/             # API роутеры
│   │   ├── mir.py           # Webhook от МИР
│   │   ├── expenses.py       # Управление расходами
│   │   ├── grants.py         # Управление грантами
│   │   └── aml.py           # AML проверки
│   └── services/            # Бизнес-логика
│       ├── blockchain.py    # Работа с блокчейном
│       ├── aml_engine.py     # AML движок
│       ├── expense_service.py
│       └── report_service.py
├── requirements.txt
└── README.md
```

## Установка

### Вариант 1: Docker Compose (рекомендуется)

1. **Скопируйте пример конфигурации:**
```bash
cp env.example .env
```

2. **Отредактируйте `.env` файл** (при необходимости)

3. **Запустите через Docker Compose:**
```bash
docker-compose up -d
```

Приложение будет доступно по адресу: http://localhost:8000

### Вариант 2: Локальная установка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**
```bash
cp env.example .env
# Отредактируйте .env файл
```

3. **Создайте базу данных PostgreSQL:**
```bash
createdb smartgrant
```

4. **Запустите приложение:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Приложение будет доступно по адресу: http://localhost:8000

**Документация API:** http://localhost:8000/docs

## API Endpoints

### МИР Webhook

**POST** `/api/v1/mir/webhook`
- Принимает транзакции от МИР
- Автоматически создаёт расходы
- Запускает AML проверку
- Логирует в блокчейн

### Гранты

- **POST** `/api/v1/grants` - Создание гранта
- **GET** `/api/v1/grants` - Список грантов
- **GET** `/api/v1/grants/{id}` - Получение гранта
- **GET** `/api/v1/grants/{id}/report` - Отчёт по гранту

### Расходы

- **POST** `/api/v1/expenses/manual` - Ручное создание расхода
- **GET** `/api/v1/expenses` - Список расходов
- **GET** `/api/v1/expenses/{id}` - Получение расхода
- **PATCH** `/api/v1/expenses/{id}` - Обновление расхода

### AML

- **POST** `/api/v1/aml/check` - Ручная AML проверка

## AML Правила

Движок проверяет следующие нарушения:

1. **large_amount** - Сумма > 20% от гранта
2. **no_receipt** - Отсутствует чек
3. **suspicious_merchant** - Название продавца похоже на ФИО
4. **affiliated_person** - Продавец аффилирован с получателем
5. **duplicated_transactions** - Дублирующиеся транзакции

## Примеры использования

### Создание гранта

```bash
curl -X POST "http://localhost:8000/api/v1/grants" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Исследовательский грант",
    "amount_total": 1000000,
    "grantee_id": 1,
    "blockchain_address": "0x123..."
  }'
```

### Webhook от МИР

```bash
curl -X POST "http://localhost:8000/api/v1/mir/webhook" \
  -H "Content-Type: application/json" \
  -d '{
    "transaction_id": "MIR-12345",
    "amount": 5000,
    "mcc": "5732",
    "merchant": "ООО УНИКАЛЬНЫЕ ДЕТАЛИ",
    "receipt": {"items": [...]}
  }'
```

### Получение отчёта по гранту

```bash
curl "http://localhost:8000/api/v1/grants/1/report"
```

## Разработка

### Запуск в режиме разработки

**С Docker:**
```bash
docker-compose up
```

**Локально:**
```bash
uvicorn app.main:app --reload
```

### Миграции БД

Используйте Alembic для миграций:

```bash
# Инициализация (если еще не инициализирован)
alembic init alembic

# Создание миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

**Примечание:** Для прототипа таблицы создаются автоматически через `Base.metadata.create_all()` в `app/main.py`

## Особенности

- ✅ Автоматическая обработка транзакций от МИР
- ✅ AML проверки в реальном времени
- ✅ Интеграция с блокчейном для прозрачности
- ✅ Детальная отчётность по грантам
- ✅ Ручная загрузка расходов с файлами
- ✅ RESTful API с автодокументацией

## TODO для продакшена

- [ ] Аутентификация и авторизация (JWT)
- [ ] Обработка файлов (сохранение, OCR)
- [ ] Интеграция с реальным смарт-контрактом
- [ ] Логирование и мониторинг
- [ ] Тесты
- [ ] Docker контейнеризация
- [ ] CI/CD

## Лицензия

MIT

# SmartGrant Backend API

Backend платформы SmartGrant для управления грантовыми средствами с интеграцией смарт-контрактов, AML-проверками и JWT авторизацией.

## Технологии

- **Python 3.11+**
- **FastAPI** - async веб-фреймворк
- **SQLAlchemy 2.0** - async ORM
- **Alembic** - миграции БД
- **PostgreSQL** - база данных
- **JWT** - авторизация
- **Web3.py** - работа с блокчейном (mock adapter)

## Структура проекта

```
backend/
├── app/
│   ├── main.py              # Точка входа FastAPI
│   ├── core/                # Конфигурация и безопасность
│   │   ├── config.py
│   │   └── security.py
│   ├── db/                  # Настройка БД
│   │   └── base.py
│   ├── models/              # SQLAlchemy модели
│   ├── schemas/             # Pydantic схемы
│   ├── services/            # Бизнес-логика
│   ├── api/                 # API роутеры
│   │   ├── auth.py
│   │   ├── government.py
│   │   ├── university.py
│   │   └── grantee.py
│   └── utils/               # Утилиты
├── alembic/                 # Миграции
├── Dockerfile
├── docker-compose.yaml
├── requirements.txt
└── README.md
```

## Быстрый старт

### Вариант 1: Docker Compose (рекомендуется)

1. **Скопируйте конфигурацию:**
```bash
cp .env.example .env
```

2. **Запустите через Docker Compose:**
```bash
docker-compose up -d
```

3. **Примените миграции:**
```bash
docker-compose exec app alembic upgrade head
```

Приложение будет доступно по адресу: http://localhost:8000

### Вариант 2: Локальная установка

1. **Установите зависимости:**
```bash
pip install -r requirements.txt
```

2. **Настройте переменные окружения:**
```bash
cp .env.example .env
# Отредактируйте .env
```

3. **Запустите PostgreSQL:**
```bash
# Убедитесь, что PostgreSQL запущен
createdb smartgrant
```

4. **Примените миграции:**
```bash
alembic upgrade head
```

5. **Запустите приложение:**
```bash
uvicorn app.main:app --reload
```

## API Endpoints

### Аутентификация

- **POST** `/api/auth/signup` - Регистрация
- **POST** `/api/auth/login` - Вход (получение JWT)

### Government (Правительство)

- **POST** `/api/government/grants` - Создание гранта

### University (Университет)

- **GET** `/api/university/grants/{id}` - Получение гранта
- **GET** `/api/university/grants/{id}/requests` - Запросы по гранту
- **POST** `/api/university/requests/{id}/approve_top3` - Одобрение топ-3
- **GET** `/api/university/logs` - Логи операций

### Grantee (Грантополучатель)

- **GET** `/api/grantee/grants` - Список грантов
- **POST** `/api/grantee/grants/{id}/spending_items` - Создание мета-пунктов
- **POST** `/api/grantee/spending_requests` - Создание запроса на транш
- **POST** `/api/grantee/spending_requests/{id}/upload_receipt` - Загрузка чека

## Примеры запросов

### 1. Регистрация пользователя

```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "government@example.com",
    "password": "password123",
    "name": "Government User",
    "role": "government"
  }'
```

### 2. Вход и получение JWT

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "government@example.com",
    "password": "password123"
  }'
```

Ответ:
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer"
}
```

### 3. Создание гранта (Government)

```bash
curl -X POST "http://localhost:8000/api/government/grants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "title": "Research Grant 2024",
    "total_amount": 1000000,
    "university_id": 2
  }'
```

### 4. Создание мета-пунктов (Grantee)

```bash
curl -X POST "http://localhost:8000/api/grantee/grants/1/spending_items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '[
    {
      "title": "Equipment",
      "planned_amount": 500000,
      "priority_index": 1
    },
    {
      "title": "Personnel",
      "planned_amount": 300000,
      "priority_index": 2
    },
    {
      "title": "Materials",
      "planned_amount": 200000,
      "priority_index": 3
    }
  ]'
```

### 5. Создание запроса на транш (Grantee)

```bash
curl -X POST "http://localhost:8000/api/grantee/spending_requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "spending_item_id": 1,
    "amount": 100000
  }'
```

### 6. Одобрение запроса (University)

```bash
curl -X POST "http://localhost:8000/api/university/requests/1/approve_top3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "approved": true
  }'
```

### 7. Загрузка чека (Grantee)

```bash
curl -X POST "http://localhost:8000/api/grantee/spending_requests/1/upload_receipt" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@receipt.pdf"
```

## Бизнес-правила

1. **Чек обязателен**: Нельзя запросить новый транш, пока не загружен и не верифицирован чек предыдущего
2. **Топ-3 требуют одобрения**: Топ-3 самых больших мета-пункта требуют ручного подтверждения университета
3. **AML проверки**: Автоматическая проверка на large_amount, duplicated_transactions, budget_exceeded
4. **Защита от double-spend**: Проверка превышения бюджета и дубликатов
5. **Логирование**: Все операции логируются в смарт-контракт (mock)

## Статусы запросов

- `pending_university_approval` - Ожидает одобрения университета (топ-3)
- `pending_receipt` - Ожидает загрузки чека
- `paid` - Оплачен
- `rejected` - Отклонён
- `blocked` - Заблокирован (AML флаги)

## Миграции

### Создание новой миграции

```bash
alembic revision --autogenerate -m "Description"
```

### Применение миграций

```bash
alembic upgrade head
```

### Откат миграции

```bash
alembic downgrade -1
```

## Документация API

После запуска документация доступна по адресу:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Тестирование

### Создание тестовых пользователей

1. Government user:
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "gov@test.com", "password": "test123", "name": "Gov User", "role": "government"}'
```

2. University user:
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "uni@test.com", "password": "test123", "name": "Uni User", "role": "university"}'
```

3. Grantee user:
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"email": "grantee@test.com", "password": "test123", "name": "Grantee User", "role": "grantee"}'
```

## Особенности

- ✅ Async/await везде
- ✅ JWT авторизация
- ✅ Ролевая модель доступа
- ✅ AML проверки
- ✅ Интеграция со смарт-контрактом (mock)
- ✅ Защита от double-spend
- ✅ Валидация бизнес-правил
- ✅ Логирование всех операций

## TODO для продакшена

- [ ] Реальная интеграция с Web3
- [ ] Обработка файлов (OCR для чеков)
- [ ] Уведомления
- [ ] Тесты
- [ ] Мониторинг и логирование
- [ ] Rate limiting
- [ ] Валидация файлов

## Лицензия

MIT


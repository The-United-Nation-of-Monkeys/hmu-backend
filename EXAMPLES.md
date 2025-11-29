# Примеры запросов к API

## Настройка

Все запросы требуют базовый URL: `http://localhost:8000`

Для запросов, требующих авторизации, используйте заголовок:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## 1. Регистрация пользователей

### Government User
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

### University User
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "university@example.com",
    "password": "password123",
    "name": "University User",
    "role": "university"
  }'
```

### Grantee User
```bash
curl -X POST "http://localhost:8000/api/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "grantee@example.com",
    "password": "password123",
    "name": "Grantee User",
    "role": "grantee"
  }'
```

## 2. Вход и получение JWT

```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "government@example.com",
    "password": "password123"
  }'
```

**Ответ:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

Сохраните `access_token` для последующих запросов.

## 3. Создание гранта (Government)

```bash
export GOV_TOKEN="YOUR_GOVERNMENT_JWT_TOKEN"

curl -X POST "http://localhost:8000/api/government/grants" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GOV_TOKEN" \
  -d '{
    "title": "Research Grant 2024",
    "total_amount": 1000000,
    "university_id": 2
  }'
```

**Ответ:**
```json
{
  "id": 1,
  "title": "Research Grant 2024",
  "total_amount": "1000000.00",
  "amount_spent": "0.00",
  "university_id": 2,
  "state": "active",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 4. Создание мета-пунктов расходов (Grantee)

```bash
export GRANTEE_TOKEN="YOUR_GRANTEE_JWT_TOKEN"

curl -X POST "http://localhost:8000/api/grantee/grants/1/spending_items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRANTEE_TOKEN" \
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

## 5. Создание запроса на транш (Grantee)

```bash
curl -X POST "http://localhost:8000/api/grantee/spending_requests" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $GRANTEE_TOKEN" \
  -d '{
    "spending_item_id": 1,
    "amount": 100000
  }'
```

**Ответ:**
```json
{
  "id": 1,
  "spending_item_id": 1,
  "grantee_id": 3,
  "amount": "100000.00",
  "status": "pending_university_approval",
  "aml_flags": [],
  "approved_by_university": null,
  "paid_tx_hash": null,
  "rejection_reason": null,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": null
}
```

## 6. Одобрение запроса (University)

```bash
export UNI_TOKEN="YOUR_UNIVERSITY_JWT_TOKEN"

curl -X POST "http://localhost:8000/api/university/requests/1/approve_top3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNI_TOKEN" \
  -d '{
    "approved": true
  }'
```

Для отклонения:
```bash
curl -X POST "http://localhost:8000/api/university/requests/1/approve_top3" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $UNI_TOKEN" \
  -d '{
    "approved": false,
    "rejection_reason": "Insufficient documentation"
  }'
```

## 7. Загрузка чека (Grantee)

```bash
curl -X POST "http://localhost:8000/api/grantee/spending_requests/1/upload_receipt" \
  -H "Authorization: Bearer $GRANTEE_TOKEN" \
  -F "file=@/path/to/receipt.pdf"
```

**Ответ:**
```json
{
  "id": 1,
  "spending_request_id": 1,
  "file_path": "./uploads/1_abc123.pdf",
  "uploaded_by": 3,
  "verified": false,
  "verified_at": null,
  "created_at": "2024-01-01T00:00:00Z"
}
```

## 8. Получение гранта (University)

```bash
curl -X GET "http://localhost:8000/api/university/grants/1" \
  -H "Authorization: Bearer $UNI_TOKEN"
```

## 9. Получение запросов по гранту (University)

```bash
curl -X GET "http://localhost:8000/api/university/grants/1/requests" \
  -H "Authorization: Bearer $UNI_TOKEN"
```

## 10. Получение логов операций (University)

```bash
curl -X GET "http://localhost:8000/api/university/logs?limit=50" \
  -H "Authorization: Bearer $UNI_TOKEN"
```

## 11. Получение грантов грантополучателя

```bash
curl -X GET "http://localhost:8000/api/grantee/grants" \
  -H "Authorization: Bearer $GRANTEE_TOKEN"
```

## Полный сценарий использования

1. **Регистрация всех пользователей** (см. раздел 1)
2. **Вход и получение токенов** (см. раздел 2)
3. **Government создаёт грант** (см. раздел 3)
4. **Grantee создаёт мета-пункты** (см. раздел 4)
5. **Grantee создаёт запрос на транш** (см. раздел 5)
6. **University одобряет запрос** (если топ-3) (см. раздел 6)
7. **Grantee загружает чек** (см. раздел 7)
8. **После верификации чека можно создать следующий запрос**

## Обработка ошибок

### 401 Unauthorized
Токен отсутствует или невалиден. Повторите вход.

### 403 Forbidden
Недостаточно прав. Проверьте роль пользователя.

### 400 Bad Request
Ошибка валидации данных. Проверьте формат запроса.

### 404 Not Found
Ресурс не найден. Проверьте ID.

## Примечания

- Все суммы в Decimal формате
- Даты в ISO 8601 формате
- Файлы ограничены 10MB
- JWT токены действительны 30 минут (по умолчанию)


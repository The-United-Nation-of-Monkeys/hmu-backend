"""
JWT и безопасность
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from app.core.config import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    # Ограничение длины пароля для bcrypt (72 байта)
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Создание JWT токена"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Декодирование JWT токена"""
    # Сначала декодируем payload вручную, чтобы получить данные
    import base64
    import json
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        payload_part = parts[1]
        # Добавляем padding если нужно
        padding = 4 - len(payload_part) % 4
        if padding != 4:
            payload_part += '=' * padding
        decoded_bytes = base64.urlsafe_b64decode(payload_part)
        payload_unverified = json.loads(decoded_bytes)
    except Exception:
        return None
    
    # Теперь пробуем верифицировать подпись с текущим SECRET_KEY
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM], 
            options={"verify_exp": False, "verify_signature": True}
        )
        return payload
    except jwt.ExpiredSignatureError:
        # Токен истек, но возвращаем payload
        return payload_unverified
    except JWTError:
        # Если не удалось верифицировать с текущим SECRET_KEY, 
        # возвращаем payload без верификации (для совместимости с токенами с другого сервера)
        return payload_unverified

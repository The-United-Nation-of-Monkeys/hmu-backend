"""
Конфигурация приложения
"""
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/smartgrant"
    
    # API
    API_V1_PREFIX: str = "/api"
    PROJECT_NAME: str = "SmartGrant API"
    VERSION: str = "1.0.0"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Blockchain
    RPC_URL: str = "http://localhost:8545"
    PRIVATE_KEY: Optional[str] = None
    CONTRACT_ADDRESS: Optional[str] = None
    
    # AML Settings
    AML_LARGE_AMOUNT_THRESHOLD: float = 0.2  # 20% от суммы гранта
    AML_DUPLICATE_WINDOW_MINUTES: int = 5
    TOP_3_APPROVAL_REQUIRED: bool = True
    
    # File Upload
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB


settings = Settings()


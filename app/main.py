"""
Главный файл FastAPI приложения
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import mir, expenses, grants, aml
from app.db import engine, Base

# Создание таблиц БД (только при запуске, не в production)
# В production используйте миграции Alembic
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    # Игнорируем ошибки подключения к БД при импорте
    # Таблицы будут созданы при первом запросе или через миграции
    pass

# Создание приложения
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API для платформы SmartGrant - управления грантовыми средствами"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(mir.router, prefix=settings.API_V1_PREFIX, tags=["МИР Webhook"])
app.include_router(expenses.router, prefix=settings.API_V1_PREFIX, tags=["Расходы"])
app.include_router(grants.router, prefix=settings.API_V1_PREFIX, tags=["Гранты"])
app.include_router(aml.router, prefix=settings.API_V1_PREFIX, tags=["AML"])


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "message": "SmartGrant API",
        "version": settings.VERSION,
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


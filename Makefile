.PHONY: help install run test docker-up docker-down docker-build clean

help:
	@echo "Доступные команды:"
	@echo "  make install     - Установить зависимости"
	@echo "  make run         - Запустить приложение"
	@echo "  make docker-up   - Запустить Docker Compose"
	@echo "  make docker-down - Остановить Docker Compose"
	@echo "  make docker-build- Пересобрать Docker образы"
	@echo "  make clean       - Очистить кэш и временные файлы"

install:
	pip install -r requirements.txt

run:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-build:
	docker-compose build --no-cache

clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +

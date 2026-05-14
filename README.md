# AI FAQ Bot API

**Вариант 4: AI FAQ Bot** — мини веб-приложение для генерации ответов на вопросы с использованием модели **T-lite-it-2.1-GGUF** (Hugging Face).

## Описание проекта

Сервис принимает текстовые вопросы, обрабатывает их с помощью квантованной GGUF-модели `t-tech/T-lite-it-2.1-GGUF`, сохраняет историю запросов в PostgreSQL и предоставляет доступ через REST API.

> **Важно:** Модель загружается **локально** из папки `models/` — не требует интернета при запуске!

## Стек технологий

- **Python 3.11** + **FastAPI**
- **PostgreSQL 16**
- **Docker / Docker Compose**
- **llama-cpp-python** (для GGUF inference)
- **SQLAlchemy** + **Pydantic**

## Быстрый старт

### 1. Подготовка модели (один раз)

Скачай модель с Hugging Face и положи в папку `models/`:

```bash
# Создай папку для модели
mkdir -p models

# Скачай модель (вариант 1: через браузер)
# Перейди на https://huggingface.co/t-tech/T-lite-it-2.1-GGUF
# Скачай файл: T-lite-it-2.1-Q4_K_M.gguf
# Положи его в папку models/

# Или через командную строку (если есть huggingface-cli):
huggingface-cli download t-tech/T-lite-it-2.1-GGUF T-lite-it-2.1-Q4_K_M.gguf --local-dir models/
```

Проверь, что файл на месте:
```bash
ls -lh models/
# Должно быть: T-lite-it-2.1-Q4_K_M.gguf (~1.3 GB)
```

### 2. Настройка окружения

```bash
cp .env.example .env
# При необходимости отредактируй .env
```

### 3. Запуск через Docker Compose

```bash
docker compose up --build
```

> **Без скачивания модели** — она берётся локально из `models/`!

### 4. Проверка работы

```bash
# Health check
curl http://localhost:8000/health

# Отправить вопрос
curl -X POST http://localhost:8000/api/v1/analyze   -H "Content-Type: application/json"   -d '{"text": "Что такое Docker?"}'

# Получить историю
curl http://localhost:8000/api/v1/history
```

### 5. Документация API

Открой в браузере: **http://localhost:8000/docs** (Swagger UI)

## Структура проекта

```
ai-faq-bot/
├── models/                          ← СЮДА КЛАДЁШЬ .gguf файл
│   ├── .gitkeep
│   └── T-lite-it-2.1-Q4_K_M.gguf  ← твоя модель (~1.3 GB)
├── app/
│   ├── main.py           # Точка входа FastAPI
│   ├── config.py         # Конфигурация из .env
│   ├── db.py             # Подключение к PostgreSQL
│   ├── models.py         # SQLAlchemy модели
│   ├── schemas.py        # Pydantic схемы
│   ├── ml_service.py     # Загрузка и инференс модели (локально!)
│   ├── logger.py         # Логирование
│   └── routes/
│       ├── analyze.py    # POST /analyze
│       ├── history.py    # GET /history, GET /history/{id}
│       └── health.py     # GET /health
├── postman/
│   └── collection.json   # Postman коллекция
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## API Endpoints

| Метод | Endpoint | Описание |
|-------|----------|----------|
| `GET` | `/` | Информация об API |
| `GET` | `/health` | Проверка состояния сервиса |
| `POST` | `/api/v1/analyze` | Отправить вопрос боту |
| `GET` | `/api/v1/history` | История запросов (пагинация) |
| `GET` | `/api/v1/history/{id}` | Конкретная запись |

### Примеры запросов

**POST /analyze**
```json
// Request
{
  "text": "Как работает FastAPI?"
}

// Response
{
  "result": "FastAPI — это современный веб-фреймворк...",
  "model": "T-lite-it-2.1-Q4_K_M.gguf",
  "processing_time_ms": 1250.5
}
```

**GET /history**
```json
{
  "items": [
    {
      "id": 1,
      "input_text": "Как работает FastAPI?",
      "result_text": "FastAPI — это современный веб-фреймворк...",
      "model_name": "T-lite-it-2.1-Q4_K_M.gguf",
      "created_at": "2026-05-13T12:00:00"
    }
  ],
  "total": 1
}
```

**GET /health**
```json
{
  "status": "ok",
  "database": "connected",
  "model_loaded": true
}
```

## Переменные окружения (.env)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `POSTGRES_USER` | Пользователь БД | `faq_user` |
| `POSTGRES_PASSWORD` | Пароль БД | `faq_password` |
| `POSTGRES_DB` | Имя БД | `faq_db` |
| `MODEL_FILE` | Имя файла модели в `models/` | `T-lite-it-2.1-Q4_K_M.gguf` |
| `MAX_TEXT_LENGTH` | Макс. длина вопроса | `500` |
| `MAX_TOKENS` | Макс. токенов ответа | `256` |
| `N_THREADS` | Потоки CPU | `4` |
| `N_CTX` | Контекст модели | `4096` |
| `TEMPERATURE` | Температура генерации | `0.7` |
| `API_KEY` | Ключ авторизации (опционально) | `""` |

> **Если скачал модель с другим именем** — измени `MODEL_FILE` в `.env`!

## Тестирование через Postman

1. Открой Postman
2. Нажми **Import** → выбери файл `postman/collection.json`
3. Запусти коллекцию по порядку:
   - `Health Check` — проверка сервиса
   - `Analyze Text (FAQ)` — основной функционал
   - `Analyze Text - Empty` — тест валидации
   - `Get History` — проверка истории

## Docker

### Сборка и запуск

```bash
# Сборка и запуск
docker compose up --build

# Фоновый режим
docker compose up -d --build

# Просмотр логов
docker compose logs -f backend

# Остановка
docker compose down

# Полная очистка (с удалением volumes)
docker compose down -v
```

### Проверка, что модель видна в контейнере

```bash
# Зайди в контейнер
docker exec -it faq_backend bash

# Проверь, что модель на месте
ls -lh /app/models/
# Должно быть: T-lite-it-2.1-Q4_K_M.gguf

# Выйди
exit
```

## Логирование

Все события логируются в stdout:
- Запуск сервиса
- Входящие запросы
- Ошибки модели
- Ошибки базы данных
- Время обработки

## Дополнительные функции

### API Key авторизация

Установи `API_KEY` в `.env`, затем отправляй заголовок:
```bash
curl -H "X-API-KEY: your-secret-key" ...
```

### Пагинация истории

```bash
# 5 записей, начиная с 10-й
curl "http://localhost:8000/api/v1/history?limit=5&offset=10"
```

## Информация о модели

- **Модель**: [t-tech/T-lite-it-2.1-GGUF](https://huggingface.co/t-tech/T-lite-it-2.1-GGUF)
- **Тип**: Квантованная GGUF (Q4_K_M)
- **Параметры**: ~2.1B
- **Языки**: Русский, английский
- **Контекст**: 4096 токенов
- **Особенности**: Оптимизирована для CPU, быстрый инференс

## Критерии оценки (по методичке)

| Критерий | Статус |
|----------|--------|
| REST API (FastAPI) | Реализовано |
| PostgreSQL + история | Реализовано |
| Hugging Face модель | T-lite-it-2.1-GGUF (локально) |
| Docker Compose | Реализовано |
| Логирование | Реализовано |
| Обработка ошибок | 400, 404, 500 |
| Postman коллекция | В папке `/postman` |
| README.md | Данный файл |
| Структурированный проект | Папки `app/`, `routes/` |

## Автор
Студенты группы 09.07.13п1
Кузнецов Н.А и Кондыкерова Н.Т
Итоговая практическая работа по дисциплине «Разработка веб-приложений», 2026.

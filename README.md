# Random Word Telegram Bot

[English](#english) | [Русский](#русский)

---

## English

### 🌟 Overview

Random Word is a Telegram bot that sends users a random Russian word with an emoji every day. Users can
subscribe/unsubscribe from daily notifications, request additional words, or get detailed explanations of words using an
integrated AI system.

### ✨ Features

- **Daily Word Delivery**: Automatically sends random words to subscribed users at 9:00 AM Moscow time
- **Interactive Actions**:
    - Get word explanations (1⭐)
    - Request additional random words (1⭐)
- **Subscription Management**: Easy subscribe/unsubscribe functionality
- **AI-Powered Explanations**: Integration with OpenRouter AI for word definitions
- **SQLite Database**: Efficient user data storage with SQLAlchemy ORM

### 🛠️ Installation

1. Clone the repository:

```bash
git clone https://github.com/abamka2004/random-word-telegram-bot.git
cd random-word-telegram-bot
```

2. Install dependencies:

```bash
uv sync
```

3. Set up environment variables:
   Create a `.env` file with:

```env
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_TOKEN=your_openrouter_api_token
UNSPLASH_TOKEN=your_api_unsplash_token
```

4. Initialize the database:

```bash
alembic upgrade head
```

5. Run the bot:

```bash
uv run python src/main.py
```

### 📁 Project Structure

```
random-word/
├── src/
│   ├── database/
│   │   ├── db_models.py
│   │   └── db_requests.py
│   └── extra/
│       ├── config.py
│       ├── keyboards.py
│       ├── shitpost_utils.py
│       └── utils.py
├── migrations/
├── words.txt
├── main.py
└── pyproject.toml
```

### ⚙️ Configuration

- `BOT_TOKEN`: Obtain from [@BotFather](https://t.me/BotFather)
- `OPENROUTER_TOKEN`: Get from [OpenRouter](https://openrouter.ai)
- Database: SQLite (automatically created at first run)

### 📝 Notes

- The `words.txt` file is sourced from [danakt/russian-words](https://github.com/danakt/russian-words)
- Payments are processed using Telegram Stars ⭐
- Uses APScheduler for task scheduling
- Includes database migrations via Alembic

---

## Русский

### 🌟 Обзор

Random Word - это Telegram-бот, который ежедневно отправляет пользователям случайное русское слово с эмодзи.
Пользователи могут подписываться/отписываться от ежедневных уведомлений, запрашивать дополнительные слова или получать
подробные объяснения слов с помощью интегрированной AI-системы.

### ✨ Возможности

- **Ежедневная отправка слов**: Автоматическая отправка случайных слов подписанным пользователям в 9:00 по московскому
  времени
- **Интерактивные действия**:
    - Получение объяснений слов (1⭐)
    - Запрос дополнительных случайных слов (1⭐)
- **Управление подпиской**: Простая система подписки/отписки
- **AI-объяснения**: Интеграция с OpenRouter AI для получения определений слов
- **SQLite База данных**: Эффективное хранение данных пользователей с SQLAlchemy ORM

### 🛠️ Установка

1. Клонируйте репозиторий:

```bash
git clone https://github.com/abamka2004/random-word-telegram-bot.git
cd random-word-telegram-bot
```

2. Установите зависимости:

```bash
uv sync
```

3. Настройте переменные окружения:
   Создайте файл `.env` с содержимым:

```env
BOT_TOKEN=your_telegram_bot_token
OPENROUTER_TOKEN=your_openrouter_api_token
UNSPLASH_TOKEN=your_api_unsplash_token
```

4. Инициализируйте базу данных:

```bash
alembic upgrade head
```

5. Запустите бота:

```bash
uv run python src/main.py
```

### 📁 Структура проекта

```
random-word/
├── src/
│   ├── database/
│   │   ├── db_models.py
│   │   └── db_requests.py
│   └── extra/
│       ├── config.py
│       ├── keyboards.py
│       ├── shitpost_utils.py
│       └── utils.py
├── migrations/
├── words.txt
├── main.py
└── pyproject.toml
```

### ⚙️ Конфигурация

- `BOT_TOKEN`: Получите у [@BotFather](https://t.me/BotFather)
- `OPENROUTER_TOKEN`: Получите на [OpenRouter](https://openrouter.ai)
- База данных: SQLite (создается автоматически при первом запуске)

### 📝 Примечания

- Файл `words.txt` взят из [danakt/russian-words](https://github.com/danakt/russian-words)
- Платежи обрабатываются с помощью Telegram Stars ⭐
- Используется APScheduler для планирования задач
- Включены миграции базы данных через Alembic
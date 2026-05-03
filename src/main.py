import asyncio
import logging

from aiogram import Bot, Dispatcher
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.database.db_models import init_db
from src.extra.config import get_bot_token
from src.extra.explanation_utils import get_word_explanation_worker
from src.extra.word_utils import send_daily_word
from src.handlers import router

# Настройка бота
TOKEN = get_bot_token()

bot = Bot(TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] > %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


async def main() -> None:
    # Инициализация БД
    await init_db()

    # Запуск планировщика задач
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_daily_word, "cron", (bot,), hour=9, minute=0)
    scheduler.start()
    logging.info("Планировщик задач запущен")

    # Запуск обработчика запросов к Openrouter для объяснения слов
    asyncio.create_task(get_word_explanation_worker())

    # Запуск бота
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

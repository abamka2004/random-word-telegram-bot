from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot, Dispatcher
import asyncio
import logging

from src.extra.config import get_bot_token
from src.database.db_models import init_db
from src.handlers import router
from src.extra.utils import send_daily_word, update_subscribers_list

# Настройка бота
TOKEN = get_bot_token()

bot = Bot(TOKEN)
dp = Dispatcher()

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - [%(levelname)s] > %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S")


async def main() -> None:
    # Инициализация БД
    await init_db()

    # Принудительное обновление списка подписчиков
    await update_subscribers_list()

    # Запуск планировщика задач
    scheduler = AsyncIOScheduler(timezone="Europe/Moscow")
    scheduler.add_job(send_daily_word, 'cron', (bot, ), hour=9, minute=0)
    scheduler.add_job(update_subscribers_list, 'interval', hours=0, minutes=1)
    scheduler.start()
    logging.info("Планировщик задач запущен")

    # Запуск бота
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())

import logging
import random
from pathlib import Path

import emoji
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from src.database import db_requests as db
from src.database.db_models import User
from src.extra.keyboards import action_kb

# Определяем пути
project_root = Path(__file__).resolve().parent.parent.parent
words_path = project_root / "words.txt"

# Загрузка слов
try:
    with open(words_path, encoding="windows-1251") as f:
        words = f.read().splitlines()
except FileNotFoundError:
    logging.error(f"Файл со словами не найден: {words_path}")
    words = ["Ошибка"]

all_emojis = list(emoji.EMOJI_DATA.keys())


async def get_random_word() -> str:
    return random.choice(words)


async def get_random_emoji() -> str:
    return random.choice(all_emojis)


async def update_subscribers_list() -> list[User]:
    return await db.get_subscribers()


async def send_word(bot: Bot, user_id: int):
    word = await get_random_word()
    _emoji = await get_random_emoji()
    try:
        await bot.send_message(
            user_id, f"{word} {_emoji}", reply_markup=action_kb(word)
        )
    except TelegramForbiddenError:
        # Отписываем юзера, чтобы больше не тратить на него ресурсы
        await db.unsubscribe(user_id)


async def send_daily_word(bot: Bot):
    subscribers = await update_subscribers_list()
    for user in subscribers:
        try:
            await send_word(bot, user.user_id)
        except Exception as e:
            logging.error(f"Ошибка отправки пользователю {user.user_id}: {e}")

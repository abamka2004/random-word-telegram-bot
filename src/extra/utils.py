import asyncio
import logging
import random
from pathlib import Path

import emoji
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import Message
from openai import AsyncOpenAI

from src.database import db_requests as db
from src.database.db_models import User
from src.extra.config import get_openrouter_token
from src.extra.keyboards import action_kb

# Определяем пути
project_root = Path(__file__).resolve().parent.parent.parent
words_path = project_root / "words.txt"

# Загрузка слов
try:
    with open(words_path, "r", encoding="windows-1251") as f:
        words = f.read().splitlines()
except FileNotFoundError:
    logging.error(f"Файл со словами не найден: {words_path}")
    words = ["Ошибка"]

all_emojis = list(emoji.EMOJI_DATA.keys())

explanation_queue: asyncio.Queue[tuple[str, Message, str]] = asyncio.Queue()

# Настройка клиента для OpenRouter
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=get_openrouter_token(),
)


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


async def get_word_explanation(word: str) -> str | None:
    system_prompt = (
        "Ты — словарь. Давай точные и краткие определения слов без лишней информации. "
        "Используй только кириллицу и стандартную пунктуацию. "
        "Всегда старайся дать объяснение, даже если слово нестандартное или редкое."
    )

    user_prompt = f"""
    Объясни значение слова "{word}" как в словаре. Соблюдай строго следующие правила:
    1. Ответ должен быть кратким (1-3 предложения)
    2. Объяснение должно быть информативным, понятным и точным
    3. Не добавляй вступлений, заключений или дополнительных комментариев
    4. Формат: "{word} - [объяснение]"
    """

    try:
        response = await client.chat.completions.create(
            model="z-ai/glm-4.5-air:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            timeout=30.0,
            extra_body={
                "include_reasoning": False  # Явно выключаем рассуждения
            },
        )

        # Проверка на наличие контента перед вызовом .strip()
        result = response.choices[0].message.content
        return result.strip() if result else None

    except Exception as e:
        logging.error(f"OpenRouter Error: {e}")
        return None


async def get_word_explanation_worker():
    logging.info("Воркер объяснений запущен")

    while True:
        # Получаем данные из очереди
        word, info_msg, charge_id = await explanation_queue.get()

        # Получаем объяснение
        explanation = await get_word_explanation(word)

        if explanation:
            await info_msg.answer(
                f"📖 Объяснение слова <b>{word}</b>:\n\n{explanation}\n\n"
                f"<tg-spoiler>Ответ сгенерирован ИИ.</tg-spoiler>",
                parse_mode="HTML",
            )
        else:
            await db.update_payment_status(charge_id, "refundable")

            await info_msg.answer(
                f"⚠️ Извините, произошла ошибка. Можете вернуть средства с помощью команды:\n"
                f"<code>/refund {charge_id}</code>",
                parse_mode="HTML",
            )

        try:
            await info_msg.delete()
        except Exception as e:
            logging.warning(f"Ошибка при удалении сообщения: {e}")

        explanation_queue.task_done()
        await asyncio.sleep(0.5)  # Пауза, чтобы не спамить в API

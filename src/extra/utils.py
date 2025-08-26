from pathlib import Path
from typing import Optional
import logging
import random
import asyncio
import re

import aiohttp
import emoji
from aiogram import Bot

from src.database.db_requests import get_subscribers
from src.database.db_models import User
from src.extra.config import get_openrouter_token
from src.extra.keyboards import action_kb

# Список подписчиков
subscribers: list[User]

# Определяем пути
project_root = Path(__file__).resolve().parent.parent.parent
words_path = project_root / 'words.txt'

# Однократная загрузка слов в память при запуске
with open(words_path, 'r') as f:
    words = f.read().splitlines()
# Получаем список всех эмодзи из библиотеки emoji
all_emojis = list(emoji.EMOJI_DATA.keys())


async def get_random_word() -> str:
    return random.choice(words)


async def get_random_emoji() -> str:
    return random.choice(all_emojis)


async def update_subscribers_list() -> list[User]:
    global subscribers
    subscribers = await get_subscribers()

    return subscribers


async def send_word(bot: Bot, user_id: int):
    word = await get_random_word()
    _emoji = await get_random_emoji()
    await bot.send_message(user_id, f"{word} {_emoji}",
                           reply_markup=action_kb(word))


async def send_daily_word(bot: Bot):
    global subscribers

    for user in subscribers:
        try:
            await send_word(bot, user.user_id)
            logging.info(f"Сообщение отправлено пользователю {user.user_id}")
        except Exception as e:
            logging.error(f"Ошибка отправки пользователю {user.user_id}: {e}")


async def get_word_explanation(word: str) -> Optional[str]:
    # Очищаем слово от возможных эмодзи и лишних символов
    clean_word = word.split()[0].strip().lower()

    prompt = f"""
    Объясни значение слова "{clean_word}" как в словаре. Соблюдай строго следующие правила:
    1. Ответ должен быть кратким (1-3 предложения)
    2. Объяснение должно быть информативным и точным
    3. Не используй никакие специальные символы (*, [], ** и т.д.)
    4. Не добавляй вступлений, заключений или дополнительных комментариев
    5. Не используй иероглифы или другие не-кириллические символы, кроме стандартной пунктуации
    6. Формат: "{clean_word} - [объяснение]"

    Если слово имеет несколько значений, выбери наиболее распространенное.
    Если слово не существует или является опечаткой, верни "Неизвестное слово".
    """

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {get_openrouter_token()}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты — словарь. Давай точные и краткие определения слов без лишней информации. Используй только кириллицу и стандартную пунктуацию."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.3
                    },
                    timeout=aiohttp.ClientTimeout(total=30)  # Таймаут 30 секунд
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    raw_explanation = data['choices'][0]['message']['content'].strip()

                    # Постобработка ответа
                    return clean_explanation_text(raw_explanation)
                else:
                    logging.error(f"API error: {response.status}")
                    return None

    except asyncio.TimeoutError:
        logging.error("OpenRouter API timeout")
        return None
    except Exception as e:
        logging.error(f"Error getting word explanation: {e}")
        return None


def clean_explanation_text(text: str) -> str:
    # Удаляем любые не-кириллические символы (кроме пунктуации)
    text = re.sub(r"[^а-яА-ЯёЁ0-9\s.,:;!?\-]", "", text)

    return text

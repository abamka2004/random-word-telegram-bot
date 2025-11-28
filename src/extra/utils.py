from pathlib import Path
import logging
import random
import asyncio
import io

import aiohttp
import emoji
from PIL import Image, ImageDraw
from aiogram import Bot

from src.database.db_requests import get_subscribers
from src.database.db_models import User
from src.extra.config import get_openrouter_token
from src.extra.keyboards import action_kb
from src.extra.shitpost_utils import setup_font, add_text_to_image, save_image_to_bytes

# Список подписчиков
subscribers: list[User]

# Определяем пути
project_root = Path(__file__).resolve().parent.parent.parent
words_path = project_root / 'words.txt'

# Однократная загрузка слов в память при запуске
with open(words_path, 'r', encoding="windows-1251") as f:
    words = f.read().splitlines()
# Получаем список всех эмодзи из библиотеки emoji
all_emojis = list(emoji.EMOJI_DATA.keys())


async def get_random_word() -> str:
    return random.choice(words)


async def get_random_emoji() -> str:
    return random.choice(all_emojis)


async def do_random_shitpost(image: bytes) -> bytes:
    # Получаем случайные слова
    word1 = await get_random_word()
    word2 = await get_random_word()
    word3 = await get_random_word()

    # Формируем текст для щитпоста
    top_text = f"{word1.upper()} {word2.upper()}"
    bottom_text = word3.upper()

    try:
        # Открываем и подготавливаем изображение
        img = Image.open(io.BytesIO(image))
        if img.mode != 'RGB':
            img = img.convert('RGB')

        draw = ImageDraw.Draw(img)

        # Настраиваем шрифт
        font = await setup_font(top_text, img.width)

        # Добавляем текст на изображение
        add_text_to_image(draw, font, top_text, bottom_text, img.width, img.height)

        # Сохраняем результат
        return save_image_to_bytes(img)

    except Exception as e:
        logging.error(f"Ошибка при создании щитпоста: {e}")
        raise


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


async def get_word_explanation(word: str) -> str | None:
    # Очищаем слово от возможных эмодзи и лишних символов
    clean_word = word.split()[0].strip().lower()

    prompt = f"""
    Объясни значение слова "{clean_word}" как в словаре. Соблюдай строго следующие правила:
    1. Ответ должен быть кратким (1-3 предложения)
    2. Объяснение должно быть информативным и точным
    3. Не добавляй вступлений, заключений или дополнительных комментариев
    4. Формат: "{clean_word} - [объяснение]"

    Если слово имеет несколько значений, выбери наиболее распространенное.
    Если слово не получается определить, попробуй найти похожее слово или объяснить возможное значение.
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
                        "model": "x-ai/grok-4.1-fast:free",
                        "messages": [
                            {
                                "role": "system",
                                "content": "Ты — словарь. Давай точные и краткие определения слов без лишней "
                                           "информации. Используй только кириллицу и стандартную пунктуацию. "
                                           "Всегда старайся дать объяснение, даже если слово нестандартное или редкое."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0.5
                    },
                    timeout=aiohttp.ClientTimeout(total=15)
            ) as response:

                if response.status == 200:
                    data = await response.json()
                    explanation = data['choices'][0]['message']['content'].strip()

                    # Постобработка ответа
                    return explanation
                else:
                    logging.error(f"API error: {response.status}")
                    return None

    except asyncio.TimeoutError:
        logging.error("OpenRouter API timeout")
        raise
    except Exception as e:
        logging.error(f"Error getting word explanation: {e}")
        raise

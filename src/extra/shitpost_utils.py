import asyncio
import io
import logging
from pathlib import Path

import aiohttp
from PIL import Image, ImageDraw, ImageFont
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont

from src.extra.config import get_unsplash_token
from src.extra.word_utils import get_random_word

project_root = Path(__file__).resolve().parent.parent.parent

# Очередь для хранения ссылок на картинки
unsplash_queue: asyncio.Queue[dict] = asyncio.Queue()


async def _fetch_unsplash_batch(count: int = 30) -> list[dict] | None:
    """Функция делает 1 запрос к API и получает данные сразу о нескольких фото"""
    access_key = get_unsplash_token()
    # Добавляем параметр count для получения массива фото
    url = f"https://api.unsplash.com/photos/random?count={count}"
    headers = {"Authorization": f"Client-ID {access_key}"}

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    batch = []
                    for item in data:
                        batch.append(
                            {
                                "url": item["urls"]["regular"],
                                "author_info": {
                                    "author_name": item["user"]["name"],
                                    "author_url": item["user"]["links"]["html"],
                                },
                            }
                        )
                    return batch
                elif response.status in (403, 429):
                    logging.warning("Unsplash: Превышен лимит запросов API!")
                    return None
                else:
                    logging.error(f"Ошибка API Unsplash: {response.status}")
                    return None
    except Exception as e:
        logging.error(f"Ошибка при запросе к Unsplash: {e}")
        return None


async def get_unsplash_worker():
    """Фоновый воркер, который поддерживает запас ссылок в очереди"""
    logging.info("Воркер Unsplash запущен")

    while True:
        # Если в очереди осталось меньше 5 ссылок, запрашиваем новую партию
        if unsplash_queue.qsize() < 5:
            logging.info("Пополнение очереди картинок Unsplash...")
            batch = await _fetch_unsplash_batch(count=30)

            if batch:
                for item in batch:
                    await unsplash_queue.put(item)
                logging.info(
                    f"Добавлено {len(batch)} фото. Текущий размер очереди: {unsplash_queue.qsize()}"
                )
            else:
                # Если произошла ошибка (например, исчерпан лимит 50/час),
                # засыпаем на 5 минут перед следующей попыткой, чтобы не спамить API
                logging.warning("Ожидание 5 минут перед следующим запросом к Unsplash")
                await asyncio.sleep(300)

        # Проверяем размер очереди раз в 10 секунд
        await asyncio.sleep(10)


async def get_random_image() -> tuple[bytes, dict[str, str]] | tuple[None, None]:
    """Скачивает картинку по заранее подготовленной ссылке из очереди"""
    try:
        # Пытаемся получить ссылку из очереди (таймаут 15 сек на случай если очередь пуста и воркер ее пополняет)
        item = await asyncio.wait_for(unsplash_queue.get(), timeout=15.0)
    except asyncio.TimeoutError:
        logging.error("Таймаут: Очередь Unsplash пуста")
        return None, None

    image_url = item["url"]
    author_info = item["author_info"]

    try:
        # Cкачиваем саму картинку напрямую с CDN (Не тратит лимит API Unsplash)
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as img_response:
                if img_response.status == 200:
                    image_data = await img_response.read()
                    unsplash_queue.task_done()
                    return image_data, author_info
                else:
                    logging.error(
                        f"Ошибка загрузки изображения с Unsplash: {img_response.status}"
                    )
                    unsplash_queue.task_done()
                    return None, None
    except Exception as e:
        logging.error(f"Ошибка при скачивании изображения: {e}")
        unsplash_queue.task_done()
        return None, None


async def setup_font(text: str, image_width: int) -> FreeTypeFont:
    """Настраивает шрифт подходящего размера"""
    font_path = project_root / "assets" / "fonts" / "Impact.ttf"

    try:
        # Простая формула: ширина изображения делённая на количество символов
        # с ограничением минимального и максимального размера
        font_size = image_width // max(len(text), 1)  # избегаем деления на 0
        font_size = max(30, min(font_size, 200))  # Минимум 30px, максимум 200px

        return ImageFont.truetype(str(font_path), size=font_size)
    except (IOError, AttributeError):
        logging.warning("Шрифт не найден, используется стандартный")
        return ImageFont.load_default()


def add_text_to_image(
    draw: ImageDraw.ImageDraw,
    font: FreeTypeFont,
    top_text: str,
    bottom_text: str,
    image_width: int,
    image_height: int,
):
    # Получаем размеры текста
    bbox_top = draw.textbbox((0, 0), top_text, font=font)
    text_width_top = bbox_top[2] - bbox_top[0]

    bbox_bottom = draw.textbbox((0, 0), bottom_text, font=font)
    text_width_bottom = bbox_bottom[2] - bbox_bottom[0]
    text_height_bottom = bbox_bottom[3] - bbox_bottom[1]

    # Позиционируем текст
    x_top = (image_width - text_width_top) / 2
    y_top = image_height * 0.03

    x_bottom = (image_width - text_width_bottom) / 2
    y_bottom = image_height - text_height_bottom - image_height * 0.03

    # Добавляем обводку (черная тень)
    shadow_offset = 2
    draw.text(
        (x_top + shadow_offset, y_top + shadow_offset),
        top_text,
        font=font,
        fill="black",
    )
    draw.text(
        (x_bottom + shadow_offset, y_bottom + shadow_offset),
        bottom_text,
        font=font,
        fill="black",
    )

    # Добавляем основной текст (белый)
    draw.text((x_top, y_top), top_text, font=font, fill="white")
    draw.text((x_bottom, y_bottom), bottom_text, font=font, fill="white")


def save_image_to_bytes(img: ImageFile) -> bytes:
    output = io.BytesIO()
    img.save(output, format="JPEG", quality=90)
    return output.getvalue()


async def create_random_shitpost(image: bytes) -> bytes:
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
        if img.mode != "RGB":
            img = img.convert("RGB")

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

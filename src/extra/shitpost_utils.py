import io
import logging
from pathlib import Path
from typing import Optional

import aiohttp
from PIL import ImageFont, ImageDraw
from PIL.ImageFile import ImageFile
from PIL.ImageFont import FreeTypeFont

from src.extra.config import get_unsplash_token

project_root = Path(__file__).resolve().parent.parent.parent


async def get_random_image() -> Optional[bytes]:
    access_key = get_unsplash_token()
    url = "https://api.unsplash.com/photos/random"

    headers = {
        "Authorization": f"Client-ID {access_key}"
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()

                    # Получаем URL обычного размера
                    image_url = data['urls']['regular']

                    # Загружаем изображение
                    async with session.get(image_url) as img_response:
                        if img_response.status == 200:
                            image_data = await img_response.read()

                            return image_data
                        else:
                            logging.error(f"Ошибка загрузки изображения: {img_response.status}")
                            return None
                else:
                    logging.error(f"Ошибка API: {response.status}")
                    return None

    except Exception as e:
        logging.error(f"Произошла ошибка: {e}")
        return None


async def setup_font(text: str, image_width: int) -> FreeTypeFont:
    """Настраивает шрифт подходящего размера"""
    font_path = project_root / 'assets' / 'fonts' / 'Impact.ttf'

    try:
        # Простая формула: ширина изображения делённая на количество символов
        # с ограничением минимального и максимального размера
        font_size = image_width // len(text)
        font_size = max(30, min(font_size, 200))  # Минимум 30px, максимум 200px

        return ImageFont.truetype(str(font_path), size=font_size)
    except (IOError, AttributeError):
        logging.warning("Шрифт не найден, используется стандартный")
        return ImageFont.load_default()


def add_text_to_image(
        draw: ImageDraw.ImageDraw, font: FreeTypeFont, top_text: str, bottom_text: str, image_width: int, image_height: int
):
    """Добавляет текст на изображение с обводкой"""
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
    draw.text((x_top + shadow_offset, y_top + shadow_offset), top_text, font=font, fill='black')
    draw.text((x_bottom + shadow_offset, y_bottom + shadow_offset), bottom_text, font=font, fill='black')

    # Добавляем основной текст (белый)
    draw.text((x_top, y_top), top_text, font=font, fill='white')
    draw.text((x_bottom, y_bottom), bottom_text, font=font, fill='white')


def save_image_to_bytes(img: ImageFile) -> bytes:
    """Сохраняет изображение в bytes"""
    output = io.BytesIO()
    img.save(output, format='JPEG', quality=90)
    return output.getvalue()

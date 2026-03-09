from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

unsubscribe_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Отписаться ❌", callback_data="unsubscribe")
    ]
])

subscribe_kb = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="Подписаться ✅", callback_data="subscribe")
    ]
])


def action_kb(word: str) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder([
        [
            InlineKeyboardButton(text="Объяснить слово 1⭐️", callback_data=f"pay_explain_{word}", pay=True)
        ],
        [
            InlineKeyboardButton(text="Ещё слово 1⭐️", callback_data="pay_word", pay=True)
        ]
    ])
    return kb.as_markup()

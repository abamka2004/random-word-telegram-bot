from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram import Router, F
import logging

from src.extra.keyboards import subscribe_kb, unsubscribe_kb
from src.extra.utils import send_word, get_word_explanation
from src.database import db_requests as db

router = Router()


@router.message(CommandStart())
async def start(message: Message):
    user_id: int = message.from_user.id

    await db.add_new_user(user_id)

    subscription_status = await db.get_subscription_status(user_id)

    await message.answer(f"<b>Добро пожаловать в бота Рандомное слово 👻!</b>\n"
                         f"Здесь вы будете получать рандомное слово каждый день.\n\n"
                         f"Статус рассылки: {'Вы подписаны ✅' if subscription_status is True else 'Вы не подписаны ❌'}",
                         parse_mode="HTML", reply_markup=unsubscribe_kb)


@router.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):
    user_id: int = callback.from_user.id

    await db.unsubscribe(user_id)
    await callback.message.answer("<b>Вы отписались от рассылки.</b>\n\n"
                                  "Нажмите кнопку ниже или напишите /start, чтобы подписаться на рассылку 👇",
                                  parse_mode="HTML", reply_markup=subscribe_kb)
    await callback.answer()


@router.callback_query(F.data == "subscribe")
async def subscribe(callback: CallbackQuery):
    user_id: int = callback.from_user.id

    await db.subscribe(user_id)
    await callback.message.answer("<b>Вы подписались на рассылку.</b>\n\n"
                                  "Нажмите кнопку ниже, чтобы отписаться от рассылки 👇",
                                  parse_mode="HTML", reply_markup=unsubscribe_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("pay_"))
async def payment(callback: CallbackQuery):
    payment_type = callback.data.split("_")[1]

    await callback.message.answer_invoice(
        title="Объяснить" if payment_type == 'explain' else "Ещё слово",
        description=f"Приобрести {'объяснение слова' if payment_type == 'explain' else 'ещё одно слово'}",
        payload=callback.data,
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=1)]
    )
    await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(event: PreCheckoutQuery):
    await event.answer(True)


@router.message(F.successful_payment.invoice_payload == "pay_word")
async def successful_pay_word(message: Message):
    try:
        await send_word(message.bot, message.from_user.id)
    except Exception as e:
        logging.error(f"Error sending the word after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка при обработке оплаты. Можете вернуть средства с помощью /refund"
        )


@router.message(F.successful_payment.invoice_payload.startswith("pay_explain_"))
async def successful_pay_explain(message: Message):
    info = await message.answer("Пожалуйста, ожидайте...")

    try:
        word = message.successful_payment.invoice_payload.split("_")[2]

        explanation = await get_word_explanation(word)
        if explanation:
            await message.answer(
                f"📖 Объяснение слова <b>{word}</b>:\n\n{explanation}",
                parse_mode="HTML"
            )
            await message.bot.delete_message(message.from_user.id, info.message_id)
        else:
            raise Exception

    except Exception as e:
        logging.error(f"Error sending the word explanation after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка при обработке оплаты. Можете вернуть средства с помощью /refund"
        )


@router.message(Command("refund"))
async def refund(message: Message):
    try:
        await message.bot.refund_star_payment(message.from_user.id, message.text.split()[1])
    except IndexError:
        await message.answer("ℹ️ Использование команды:\n\n"
                             "/refund ваш_id_транзакции")

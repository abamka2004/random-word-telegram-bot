from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery, BufferedInputFile
from aiogram import Router, F
import logging

from src.extra.keyboards import subscribe_kb, unsubscribe_kb, shitpost_kb
from src.extra.shitpost_utils import get_random_image
from src.extra.utils import send_word, get_word_explanation, do_random_shitpost
from src.database import db_requests as db

router = Router()


### START ###

@router.message(CommandStart())
async def start(message: Message):
    user_id: int = message.from_user.id

    await db.add_new_user(user_id)

    subscription_status = await db.get_subscription_status(user_id)

    await message.answer(f"<b>Добро пожаловать в бота Рандомное слово 👻!</b>\n"
                         f"Здесь вы будете получать рандомное слово каждый день.\n\n"
                         f"Статус рассылки: {'Вы подписаны ✅' if subscription_status is True else 'Вы не подписаны ❌'}",
                         parse_mode="HTML", reply_markup=unsubscribe_kb)


### SUBSCRIPTIONS ###

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


### ACTIONS ###

@router.message(Command("word"))
async def word(message: Message):
    await message.answer_invoice(
        title="Объяснить",
        description=f"Приобрести объяснение слова",
        payload="pay_word",
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=1)]
    )


@router.message(Command("shitpost"))
async def shitpost(message: Message):
    await message.answer_invoice(
        title="Щитпост",
        description=f"Создать щитпост",
        payload="pay_shitpost",
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=3)]
    )


### PAYMENTS ###

@router.callback_query(F.data.startswith("pay_"))
async def payment(callback: CallbackQuery):
    payment_type = callback.data.split("_")[1]

    if payment_type == "explain":
        await callback.message.answer_invoice(
            title="Объяснить",
            description=f"Приобрести объяснение слова",
            payload=callback.data,
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=1)]
        )
        await callback.answer()
    elif payment_type == "word":
        await callback.message.answer_invoice(
            title="Ещё слово",
            description=f"Приобрести ещё одно слово",
            payload=callback.data,
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=1)]
        )
        await callback.answer()
    elif payment_type == "shitpost":
        await callback.message.answer_invoice(
            title="Щитпост",
            description=f"Создать щитпост",
            payload=callback.data,
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=3)]
        )
        await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(event: PreCheckoutQuery):
    await event.answer(True)


@router.message(Command("refund"))
async def refund(message: Message):
    try:
        await message.bot.refund_star_payment(message.from_user.id, message.text.split()[1])
    except IndexError:
        await message.answer("ℹ️ Использование команды:\n\n"
                             "/refund ваш_id_транзакции")


### ACTIONS PERFORMING ###

@router.message(F.successful_payment.invoice_payload == "pay_word")
async def successful_pay_word(message: Message):
    try:
        await send_word(message.bot, message.from_user.id)
    except Exception as e:
        logging.error(f"Error sending the word after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка. Можете вернуть средства с помощью /refund"
        )


@router.message(F.successful_payment.invoice_payload.startswith("pay_explain_"))
async def successful_pay_explain(message: Message):
    info = await message.answer("Пожалуйста, ожидайте...")

    try:
        word = message.successful_payment.invoice_payload.split("_")[2]

        explanation = await get_word_explanation(word)
        if explanation:
            await message.answer(
                f"📖 Объяснение слова <b>{word}</b>:\n\n{explanation}\n\n"
                f"<tg-spoiler>Ответ сгенерирован ИИ, возможны ошибки.</tg-spoiler>",
                parse_mode="HTML"
            )
            await info.delete()

    except Exception as e:
        logging.error(f"Error sending the word explanation after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка. Можете вернуть средства с помощью /refund"
        )


@router.message(F.successful_payment.invoice_payload == "pay_shitpost")
async def successful_pay_shitpost(message: Message):
    info = await message.answer("Пожалуйста, ожидайте...")

    try:
        picture_bytes, author_info = await get_random_image()

        shitpost_img = await do_random_shitpost(picture_bytes)

        if shitpost_img:
            await message.answer_photo(BufferedInputFile(shitpost_img, "shitpost.jpeg"),
                                       caption=f"<tg-spoiler>"
                                               f"автор: {author_info['name']}\n"
                                               f"{author_info['url']}"
                                               f"</tg-spoiler>",
                                       parse_mode="HTML",
                                       reply_markup=shitpost_kb)
        else:
            raise Exception

    except Exception as e:
        logging.error(f"Error sending the shitpost after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка. Можете вернуть средства с помощью /refund"
        )
    finally:
        await info.delete()

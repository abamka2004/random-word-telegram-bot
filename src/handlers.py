import logging

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, LabeledPrice, Message, PreCheckoutQuery

from src.database import db_requests as db
from src.extra.keyboards import subscribe_kb, unsubscribe_kb
from src.extra.utils import explanation_queue, send_word

router = Router()


### START ###


@router.message(CommandStart())
async def start(message: Message):
    user_id: int = message.from_user.id

    await db.add_new_user(user_id)

    subscription_status = await db.get_subscription_status(user_id)

    bot_name = await message.bot.get_my_name()
    await message.answer(
        f"<b>Добро пожаловать в бота {bot_name.name}!</b>\n"
        f"Здесь вы будете получать рандомное слово каждый день.\n\n"
        f"Статус рассылки: {'Вы подписаны ✅' if subscription_status is True else 'Вы не подписаны ❌'}",
        parse_mode="HTML",
        reply_markup=unsubscribe_kb,
    )


### SUBSCRIPTIONS ###


@router.callback_query(F.data == "unsubscribe")
async def unsubscribe(callback: CallbackQuery):
    user_id: int = callback.from_user.id

    await db.unsubscribe(user_id)
    await callback.message.answer(
        "<b>Вы отписались от рассылки.</b>\n\n"
        "Нажмите кнопку ниже или напишите /start, чтобы подписаться на рассылку 👇",
        parse_mode="HTML",
        reply_markup=subscribe_kb,
    )
    await callback.answer()


@router.callback_query(F.data == "subscribe")
async def subscribe(callback: CallbackQuery):
    user_id: int = callback.from_user.id

    await db.subscribe(user_id)
    await callback.message.answer(
        "<b>Вы подписались на рассылку.</b>\n\n"
        "Нажмите кнопку ниже, чтобы отписаться от рассылки 👇",
        parse_mode="HTML",
        reply_markup=unsubscribe_kb,
    )
    await callback.answer()


### ACTIONS ###


@router.message(Command("word"))
async def word(message: Message):
    await message.answer_invoice(
        title="Объяснить",
        description="Приобрести ещё одно слово",
        payload="pay_word",
        currency="XTR",
        prices=[LabeledPrice(label="XTR", amount=1)],
    )


### PAYMENTS ###


@router.callback_query(F.data.startswith("pay_"))
async def payment(callback: CallbackQuery):
    payment_type = callback.data.split("_")[1]

    if payment_type == "explain":
        await callback.message.answer_invoice(
            title="Объяснить",
            description="Приобрести объяснение слова",
            payload=callback.data,
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=1)],
        )
        await callback.answer()
    elif payment_type == "word":
        await callback.message.answer_invoice(
            title="Ещё слово",
            description="Приобрести ещё одно слово",
            payload=callback.data,
            currency="XTR",
            prices=[LabeledPrice(label="XTR", amount=1)],
        )
        await callback.answer()


@router.pre_checkout_query()
async def pre_checkout_handler(event: PreCheckoutQuery):
    await event.answer(True)


@router.message(Command("refund"))
async def refund(message: Message):
    args = message.text.split()
    if len(args) < 2:
        return await message.answer(
            "ℹ️ Использование: <code>/refund id_транзакции</code>", parse_mode="HTML"
        )

    charge_id = args[1]
    status = await db.get_payment_status(charge_id)

    if status is None:
        return await message.answer("❌ Транзакция не найдена.")

    if status == "success":
        return await message.answer(
            "❌ Этот платёж нельзя вернуть, так как услуга была оказана."
        )

    if status == "refunded":
        return await message.answer(
            "ℹ️ Средства за этот платёж уже были возвращены ранее."
        )

    if status == "refundable":
        try:
            await message.bot.refund_star_payment(message.from_user.id, charge_id)
            await db.update_payment_status(charge_id, "refunded")
        except Exception as e:
            logging.error(f"Refund error: {e}")
            await message.answer("❌ Произошла техническая ошибка при возврате.")


### ACTIONS PERFORMING ###


@router.message(F.successful_payment.invoice_payload == "pay_word")
async def successful_pay_word(message: Message):
    charge_id = message.successful_payment.telegram_payment_charge_id

    await db.add_payment(
        charge_id=charge_id,
        user_id=message.from_user.id,
        payload="pay_word",
        status="success",
    )

    try:
        await send_word(message.bot, message.from_user.id)
    except Exception as e:
        logging.error(f"Error sending the word after payment: {e}")
        await message.answer(
            "⚠️ Извините, произошла ошибка. Можете вернуть средства с помощью команды:\n"
            f"<code>/refund {charge_id}</code>",
            parse_mode="HTML",
        )


@router.message(F.successful_payment.invoice_payload.startswith("pay_explain_"))
async def successful_pay_explain(message: Message):
    info = await message.answer("Пожалуйста, ожидайте... 🔎")
    word = message.successful_payment.invoice_payload.split("_")[2]
    charge_id = message.successful_payment.telegram_payment_charge_id

    await db.add_payment(
        charge_id=charge_id,
        user_id=message.from_user.id,
        payload=message.successful_payment.invoice_payload,
        status="success",
    )

    # Помещаем запрос в очередь, хендлер тут же завершается, а воркер обрабатывает задачу в фоне
    await explanation_queue.put((word, info, charge_id))

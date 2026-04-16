from typing import Literal

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from src.database.db_models import Payment, User, async_session


async def add_new_user(user_id: int) -> None:
    async with async_session() as session:
        try:
            session.add(User(user_id=user_id))
            await session.commit()
        except IntegrityError:
            pass
        except Exception as e:
            await session.rollback()
            raise e


async def get_subscription_status(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.get(User, user_id)
        return user.subscription_status if user else False


async def subscribe(user_id: int) -> None:
    async with async_session() as session:
        try:
            await session.execute(
                update(User)
                .values({"subscription_status": True})
                .where(User.user_id == user_id)
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


async def unsubscribe(user_id: int) -> None:
    async with async_session() as session:
        try:
            await session.execute(
                update(User)
                .values({"subscription_status": False})
                .where(User.user_id == user_id)
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


async def get_subscribers() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.subscription_status))
        return list(result.scalars().all())


async def add_payment(
    charge_id: str,
    user_id: int,
    payload: str,
    status: Literal["success", "refundable", "refunded"] = "success",
) -> None:
    async with async_session() as session:
        try:
            session.add(
                Payment(
                    charge_id=charge_id, user_id=user_id, payload=payload, status=status
                )
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


async def update_payment_status(
    charge_id: str, new_status: Literal["success", "refundable", "refunded"]
) -> None:
    async with async_session() as session:
        try:
            await session(
                update(Payment)
                .where(Payment.charge_id == charge_id)
                .values(status=new_status)
            )
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e


async def get_payment_status(charge_id: str) -> str | None:
    async with async_session() as session:
        payment = await session.get(Payment, charge_id)
        return payment.status if payment else None

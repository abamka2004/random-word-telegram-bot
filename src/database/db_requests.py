from sqlalchemy import select, update
from sqlalchemy.exc import NoResultFound, IntegrityError

from src.database.db_models import async_session, User


async def add_new_user(user_id: int) -> None:
    async with async_session() as session:
        try:
            session.add(
                User(user_id=user_id)
            )
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
        result = await session.execute(
            select(User)
            .where(User.subscription_status == True)
        )
        return list(result.scalars().all())

import os
import pathlib
from typing import ClassVar, Literal

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    MetaData,
    String,
    func,
    text,
)
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# Настройка БД
root = pathlib.Path(__file__).parent.parent.parent
DB_PATH = os.path.join(root, "random_word.db")
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"

engine = create_async_engine(DB_URL)
async_session = async_sessionmaker(engine)


class Base(DeclarativeBase, AsyncAttrs):
    metadata: ClassVar[MetaData] = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class User(Base):
    __tablename__: str = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    subscription_status: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


class Payment(Base):
    __tablename__: str = "payments"

    charge_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id"))

    payload: Mapped[str] = mapped_column(String)

    # Статусы:
    # 'success' (выполнено), 'refundable' (можно вернуть), 'refunded' (возвращён)
    status: Mapped[Literal["success", "refundable", "refunded"]] = mapped_column(
        String, default="success"
    )

    created_at: Mapped[DateTime] = mapped_column(DateTime, server_default=func.now())


def run_migrations() -> None:
    cfg = Config("alembic.ini")
    cfg.set_main_option("script_location", "migrations")
    command.upgrade(cfg, "head")


async def init_db() -> None:
    async with engine.begin() as conn:
        # WAL режим предотвращает блокировки БД при параллельной записи
        await conn.execute(text("PRAGMA journal_mode=WAL;"))

    run_migrations()

import sys
from os.path import abspath, dirname

from alembic import context

# Добавляем путь к проекту в sys.path
sys.path.insert(0, dirname(dirname(abspath(__file__))))

from src.database.db_models import Base, create_async_engine
from src.extra.config import get_bot_token

# Используем metadata из ваших моделей
target_metadata = Base.metadata


# Функция для запуска миграций в онлайн-режиме
def run_migrations_online():
    connectable = create_async_engine(get_bot_token())

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True
        )

        with context.begin_transaction():
            context.run_migrations()

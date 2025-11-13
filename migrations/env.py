import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# --- PYTHONPATH: надежно добавляем корень и src ---
THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent  # папка migrations/.. = корень
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in map(str, sys.path):
    sys.path.append(str(SRC_DIR))

# --- Модели (метаданные) ---
from app.models import Base  # noqa: E402

# --- Alembic config ---
config = context.config

# Логи Alembic (если section [loggers]/[handlers]/[formatters] в alembic.ini есть)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# DATABASE_URL из env перекрывает alembic.ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

# Метаданные для автогенерации
target_metadata = Base.metadata

# Опции автогенерации
AUTOGEN_KW = dict(
    target_metadata=target_metadata,
    compare_type=True,
    compare_server_default=True,
    # version_table можно переименовать при необходимости проекта
    version_table="alembic_version",
)

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    if not url:
        raise RuntimeError("sqlalchemy.url is not set (env DATABASE_URL or alembic.ini)")

    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **AUTOGEN_KW,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    # читаем секцию [alembic], префикс sqlalchemy.*
    section = config.get_section(config.config_ini_section) or {}
    connectable = engine_from_config(
        section,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True,  # безопасно для SQLA 1.4+
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, **AUTOGEN_KW)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()

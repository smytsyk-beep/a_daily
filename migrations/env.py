import os
import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ---PYTHONPATH: надёжно добавляем src/ относительно корня репозитория ---
THIS_DIR = Path(__file__).resolve().parent  # .../migrations
REPO_ROOT = THIS_DIR.parent  # корень проекта
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in map(str, sys.path):
    sys.path.append(str(SRC_DIR))

# Модели (метаданные) — используются для автогенерации миграций
from app.models import Base  # noqa: E402

# --- Alembic Config с фолбэком для прямого импорта env.py ---
cfg = getattr(context, "config", None)
if cfg is None:
    # env.py импортирован напрямую (например, в тесте) — создаём Config вручную
    from alembic.config import Config

    ini_path = os.getenv("ALEMBIC_INI", str(REPO_ROOT / "alembic.ini"))
    cfg = Config(ini_path)

# Логирование Alembic из ini (если задано)
if getattr(cfg, "config_file_name", None):
    fileConfig(cfg.config_file_name)

# Если задан DATABASE_URL, он перекрывает URL из ini
database_url = os.getenv("DATABASE_URL")
if database_url:
    cfg.set_main_option("sqlalchemy.url", database_url)

# Метаданные для автогенерации
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Запуск миграций в offline-режиме (без подключения к БД)."""
    url = cfg.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Запуск миграций в online-режиме (с подключением к БД)."""
    connectable = engine_from_config(
        cfg.get_section(cfg.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


def _maybe_run_under_alembic() -> None:
    try:
        is_offline = context.is_offline_mode()
    except Exception:
        return
    if is_offline:
        run_migrations_offline()
    else:
        run_migrations_online()


_maybe_run_under_alembic()

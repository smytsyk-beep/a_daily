import os
import uuid
import subprocess
import psycopg2
from psycopg2 import extensions, sql

# Админ-подключение к системной БД, из которой можно создавать/удалять другие БД
PG_DSN_ADMIN = "host=db port=5432 user=astrodaily password=astrodaily dbname=postgres"


def _create_db(name: str) -> None:
    """Создать временную БД вне транзакции (AUTOCOMMIT)."""
    conn = psycopg2.connect(PG_DSN_ADMIN)
    try:
        # оба способа, чтобы наверняка
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        finally:
            cur.close()
    finally:
        conn.close()


def _drop_db(name: str) -> None:
    """Завершить подключения к БД и удалить её вне транзакции (AUTOCOMMIT)."""
    conn = psycopg2.connect(PG_DSN_ADMIN)
    try:
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
        conn.autocommit = True
        cur = conn.cursor()
        try:
            # Завершаем все активные подключения к удаляемой БД
            cur.execute(
                "SELECT pg_terminate_backend(pid) "
                "FROM pg_stat_activity WHERE datname = %s AND pid <> pg_backend_pid()",
                (name,),
            )
            cur.execute(sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name)))
        finally:
            cur.close()
    finally:
        conn.close()


def _alembic_run(args: list[str], database_url: str) -> None:
    """Запустить Alembic с подменой DATABASE_URL."""
    env = os.environ.copy()
    env["DATABASE_URL"] = database_url
    subprocess.run(
        ["alembic", "-c", "/app/alembic.ini", *args],
        check=True,
        env=env,
        cwd="/app",
    )


def _table_exists(dbname: str, table: str) -> bool:
    """Проверить наличие таблицы в public-схеме."""
    dsn = f"host=db port=5432 user=astrodaily password=astrodaily dbname={dbname}"
    conn = psycopg2.connect(dsn)
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                SELECT EXISTS (
                    SELECT 1
                    FROM information_schema.tables
                    WHERE table_schema = 'public' AND table_name = %s
                );
                """,
                (table,),
            )
            (exists,) = cur.fetchone()
            return bool(exists)
        finally:
            cur.close()
    finally:
        conn.close()


def test_alembic_roundtrip():
    tmp_db = f"alembic_tmp_{uuid.uuid4().hex[:8]}"
    db_url = f"postgresql+psycopg2://astrodaily:astrodaily@db:5432/{tmp_db}"

    _create_db(tmp_db)
    try:
        # upgrade head
        _alembic_run(["upgrade", "head"], db_url)
        assert _table_exists(tmp_db, "users")

        # downgrade base
        _alembic_run(["downgrade", "base"], db_url)
        assert not _table_exists(tmp_db, "users")

        # снова upgrade head
        _alembic_run(["upgrade", "head"], db_url)
        assert _table_exists(tmp_db, "users")
    finally:
        _drop_db(tmp_db)
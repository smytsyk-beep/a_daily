import os
import uuid
import subprocess
from pathlib import Path

import psycopg2
from psycopg2 import sql, extensions


# Унифицируем хост/порты: в докере host=db, в CI host=localhost
IN_DOCKER = Path("/app").exists()
HOST = os.getenv("PGHOST") or ("db" if IN_DOCKER else "localhost")
# HOST = os.getenv("PGHOST", "db")

PORT = int(os.getenv("PGPORT", "5432"))

PG_USER = os.getenv("PGUSER", "astrodaily")
PG_PASS = os.getenv("PGPASSWORD", "astrodaily")

PG_DSN_ADMIN = (
    f"host={HOST} port={PORT} user={PG_USER} password={PG_PASS} dbname=postgres"
)

REPO_ROOT = Path(__file__).resolve().parents[1]
ALEMBIC_INI = REPO_ROOT / "alembic.ini"


def _enable_autocommit(conn):
    """Надёжно включаем autocommit во всех окружениях."""
    try:
        # если вдруг транзакция уже открыта – гасим её
        conn.rollback()
    except Exception:
        pass
    try:
        conn.set_session(autocommit=True)
    except Exception:
        pass
    try:
        conn.autocommit = True
    except Exception:
        pass
    try:
        conn.set_isolation_level(extensions.ISOLATION_LEVEL_AUTOCOMMIT)
    except Exception:
        pass


def _create_db(name: str) -> None:
    conn = psycopg2.connect(PG_DSN_ADMIN)
    try:
        _enable_autocommit(conn)
        with conn.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    finally:
        conn.close()


def _drop_db(name: str) -> None:
    conn = psycopg2.connect(PG_DSN_ADMIN)
    try:
        _enable_autocommit(conn)
        with conn.cursor() as cur:
            # на всякий случай отключаем активные коннекты к БД
            cur.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                (name,),
            )
            cur.execute(
                sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name))
            )
    finally:
        conn.close()


def _alembic_run(args, db_url: str):
    env = os.environ.copy()
    env["DATABASE_URL"] = db_url
    env["ALEMBIC_INI"] = str(ALEMBIC_INI)

    # В докере cwd=/app, в CI — корень репо
    cwd = "/app" if Path("/app/alembic.ini").exists() else str(REPO_ROOT)

    subprocess.run(
        ["alembic", "-c", str(ALEMBIC_INI), *args],
        check=True,
        cwd=cwd,
        env=env,
    )


def test_alembic_roundtrip():
    tmp_db = f"alembic_tmp_{uuid.uuid4().hex[:8]}"
    db_url = f"postgresql+psycopg2://{PG_USER}:{PG_PASS}@{HOST}:{PORT}/{tmp_db}"

    _create_db(tmp_db)
    try:
        _alembic_run(["upgrade", "head"], db_url)
        _alembic_run(["downgrade", "base"], db_url)
    finally:
        _drop_db(tmp_db)

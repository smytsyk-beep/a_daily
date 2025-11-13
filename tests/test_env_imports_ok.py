from pathlib import Path
import importlib.util
import os


def test_env_imports_ok(monkeypatch):
    # Определяем корень репозитория: .../tests/ -> parents[1]
    repo_root = Path(__file__).resolve().parents[1]
    alembic_ini = repo_root / "alembic.ini"
    env_py = repo_root / "migrations" / "env.py"

    assert env_py.exists(), f"env.py not found at {env_py}"
    assert alembic_ini.exists(), f"alembic.ini not found at {alembic_ini}"

    # Подсказываем env.py путь к ini и убираем DATABASE_URL, чтобы не перекрывал ini
    monkeypatch.setenv("ALEMBIC_INI", str(alembic_ini))
    monkeypatch.delenv("DATABASE_URL", raising=False)

    spec = importlib.util.spec_from_file_location("migrations.env", str(env_py))
    assert spec and spec.loader, "spec/loader not created"

    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # импорт не должен падать

    assert hasattr(m, "run_migrations_online")
    assert hasattr(m, "run_migrations_offline")
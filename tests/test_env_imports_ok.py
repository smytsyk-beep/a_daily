def test_env_imports_ok(monkeypatch):
    # На всякий случай подскажем env.py где лежит ini
    monkeypatch.setenv("ALEMBIC_INI", "/app/alembic.ini")
    # И уберём DATABASE_URL, чтобы он не перекрывал ini в этом тесте
    monkeypatch.delenv("DATABASE_URL", raising=False)

    import importlib.util, pathlib

    path = pathlib.Path("/app/migrations/env.py")
    spec = importlib.util.spec_from_file_location("migrations.env", str(path))
    assert spec and spec.loader, "spec/loader not created"

    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # импорт не должен падать

    assert hasattr(m, "run_migrations_online")
    assert hasattr(m, "run_migrations_offline")
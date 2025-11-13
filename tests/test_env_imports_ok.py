
def test_env_imports_ok():
    import importlib.util, pathlib
    spec = importlib.util.spec_from_file_location(
        "migrations.env", str(pathlib.Path("/app/migrations/env.py"))
    )
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)  # не должен упасть
    assert hasattr(m, "run_migrations_online")
    assert hasattr(m, "run_migrations_offline")
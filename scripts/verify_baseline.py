#!/usr/bin/env python3
"""Reproduce the audited AstroDaily baseline against disposable PostgreSQL 16."""

from __future__ import annotations

import configparser
import json
import os
import re
import secrets
import signal
import subprocess
import sys
import tempfile
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import quote

import psycopg2


REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
MANIFEST_PATH = REPO_ROOT / "scripts" / "baseline_known_drift.json"
POSTGRES_IMAGE = "postgres:16"
POSTGRES_DATA_DIR = "/var/lib/postgresql/data"
RESOURCE_LABEL = "com.astrodaily.baseline.id"
EXPECTED_TEST_COUNT = 299
COMMAND_TIMEOUT_SECONDS = 300
TIMEZONE_FILES = {
    "UTC": "Etc/UTC",
    "Europe/Berlin": "Europe/Berlin",
    "Europe/Kyiv": "Europe/Kyiv",
    "Europe/London": "Europe/London",
    "Europe/Moscow": "Europe/Moscow",
    "America/Los_Angeles": "America/Los_Angeles",
    "America/New_York": "America/New_York",
}


class BaselineError(RuntimeError):
    """A verification step failed or could not be classified safely."""


class BaselineInterrupted(BaselineError):
    """The runner received an interruption signal."""


@dataclass(frozen=True)
class DatabaseTarget:
    identity: str
    container_name: str
    network_name: str
    database: str
    username: str
    password: str
    host: str = "127.0.0.1"
    port: int | None = None

    @property
    def sqlalchemy_url(self) -> str:
        if self.port is None:
            raise BaselineError("PostgreSQL host port has not been assigned")
        return (
            "postgresql+psycopg2://"
            f"{quote(self.username)}:{quote(self.password)}"
            f"@{self.host}:{self.port}/{quote(self.database)}"
        )

    def connection_kwargs(self, database: str | None = None) -> dict[str, Any]:
        if self.port is None:
            raise BaselineError("PostgreSQL host port has not been assigned")
        return {
            "host": self.host,
            "port": self.port,
            "user": self.username,
            "password": self.password,
            "dbname": database or self.database,
            "connect_timeout": 2,
        }


def _print_step(number: int, message: str) -> None:
    print(f"\n[{number}/12] {message}", flush=True)


def _run(
    args: list[str],
    *,
    cwd: Path,
    env: dict[str, str],
    display: str,
    check: bool = True,
    timeout: int = COMMAND_TIMEOUT_SECONDS,
) -> subprocess.CompletedProcess[str]:
    print(f"$ {display}", flush=True)
    result = subprocess.run(
        args,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=timeout,
        check=False,
    )
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if check and result.returncode != 0:
        raise BaselineError(
            f"Command failed with exit code {result.returncode}: {display}"
        )
    return result


def _docker(
    args: list[str],
    *,
    check: bool = True,
    timeout: int = 120,
    cwd: Path = REPO_ROOT,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["docker", *args],
        cwd=cwd,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()
        raise BaselineError(f"Docker command failed: {detail}")
    return result


def _sanitized_base_env() -> dict[str, str]:
    secret_markers = ("PASSWORD", "TOKEN", "SECRET", "API_KEY", "DATABASE_URL")
    env = {
        key: value
        for key, value in os.environ.items()
        if not any(marker in key.upper() for marker in secret_markers)
        and not key.upper().startswith("PG")
    }
    executable_dir = str(Path(sys.executable).resolve().parent)
    env["PATH"] = executable_dir + os.pathsep + env.get("PATH", "")
    env["PYTHONPATH"] = str(REPO_ROOT / "src")
    env.update(
        {
            "APP_ENV": "test",
            "APP_NAME": "astrodaily-baseline",
            "APP_HOST": "127.0.0.1",
            "APP_PORT": "8080",
            "DEBUG": "false",
            "SQLALCHEMY_ECHO": "false",
            "LOG_LEVEL": "WARNING",
            "ASTRO_EPHEMERIS_DIR": str(REPO_ROOT / "data" / "ephemeris"),
            "ASTRO_EPHEMERIS_FILE": "de440s.bsp",
            "GEOCODER_MODE": "stub",
            "GEOCODER_CACHE_TTL_DAYS": "3650",
            "NOMINATIM_BASE_URL": "http://127.0.0.1.invalid",
            "NOMINATIM_TIMEOUT_S": "1",
            "GOOGLE_GEOCODING_TIMEOUT_S": "1",
            "LLM_PROVIDER": "openai",
            "LLM_MODEL": "disabled-for-baseline",
            "LLM_ENABLED": "false",
            "LLM_CACHE_TTL_DAYS": "7",
            "LLM_MAX_DAILY_COST_USD": "0",
            "LLM_MAX_MONTHLY_COST_USD": "0",
            "AB_DIGEST_LLM_PERCENT": "0",
        }
    )
    return env


def _database_env(base_env: dict[str, str], target: DatabaseTarget) -> dict[str, str]:
    if target.port is None:
        raise BaselineError("PostgreSQL host port has not been assigned")
    env = base_env.copy()
    env.update(
        {
            "DATABASE_URL": target.sqlalchemy_url,
            "POSTGRES_HOST": target.host,
            "POSTGRES_PORT": str(target.port),
            "POSTGRES_DB": target.database,
            "POSTGRES_USER": target.username,
            "POSTGRES_PASSWORD": target.password,
            "PGHOST": target.host,
            "PGPORT": str(target.port),
            "PGUSER": target.username,
            "PGPASSWORD": target.password,
        }
    )
    return env


def _write_isolated_alembic_config(directory: Path) -> Path:
    source = REPO_ROOT / "alembic.ini"
    parser = configparser.ConfigParser()
    parser.read(source, encoding="utf-8")
    parser.set("alembic", "script_location", str(REPO_ROOT / "migrations"))
    parser.set("alembic", "prepend_sys_path", str(REPO_ROOT))
    destination = directory / "alembic.ini"
    with destination.open("w", encoding="utf-8") as handle:
        parser.write(handle)
    return destination


def _make_target() -> DatabaseTarget:
    suffix = uuid.uuid4().hex[:12]
    identity = f"issue33-{suffix}"
    safe_suffix = suffix.lower()
    return DatabaseTarget(
        identity=identity,
        container_name=f"astrodaily-baseline-pg-{safe_suffix}",
        network_name=f"astrodaily-baseline-net-{safe_suffix}",
        database=f"baseline_{safe_suffix}",
        username=f"baseline_{safe_suffix}",
        password=secrets.token_urlsafe(24),
    )


def _check_docker_available() -> None:
    result = _docker(["version", "--format", "{{.Server.Version}}"], check=False)
    if result.returncode != 0 or not result.stdout.strip():
        raise BaselineError(
            "Docker daemon is unavailable. Start Docker and rerun; "
            "the baseline will not fall back to another database."
        )
    print(f"Docker daemon available (server {result.stdout.strip()})")


def _create_postgres(target: DatabaseTarget) -> DatabaseTarget:
    _docker(
        [
            "network",
            "create",
            "--label",
            f"{RESOURCE_LABEL}={target.identity}",
            target.network_name,
        ]
    )
    _docker(
        [
            "run",
            "--detach",
            "--name",
            target.container_name,
            "--label",
            f"{RESOURCE_LABEL}={target.identity}",
            "--network",
            target.network_name,
            "--tmpfs",
            f"{POSTGRES_DATA_DIR}:rw,noexec,nosuid,size=512m",
            "--publish",
            "127.0.0.1::5432",
            "--env",
            f"POSTGRES_DB={target.database}",
            "--env",
            f"POSTGRES_USER={target.username}",
            "--env",
            f"POSTGRES_PASSWORD={target.password}",
            POSTGRES_IMAGE,
        ],
        timeout=300,
    )
    port_result = _docker(["port", target.container_name, "5432/tcp"])
    match = re.search(r"127\.0\.0\.1:(\d+)", port_result.stdout)
    if not match:
        raise BaselineError("Could not resolve the disposable PostgreSQL host port")
    return DatabaseTarget(**{**target.__dict__, "port": int(match.group(1))})


def _verify_docker_identity(target: DatabaseTarget) -> None:
    inspect_result = _docker(["inspect", target.container_name])
    payload = json.loads(inspect_result.stdout)[0]
    labels = payload.get("Config", {}).get("Labels") or {}
    if labels.get(RESOURCE_LABEL) != target.identity:
        raise BaselineError("Container baseline identity label does not match")
    if payload.get("Name") != f"/{target.container_name}":
        raise BaselineError("Container name does not match generated baseline identity")
    if payload.get("Config", {}).get("Image") != POSTGRES_IMAGE:
        raise BaselineError("Disposable database is not using postgres:16")
    tmpfs = payload.get("HostConfig", {}).get("Tmpfs") or {}
    if POSTGRES_DATA_DIR not in tmpfs:
        raise BaselineError("PostgreSQL data directory is not backed by tmpfs")
    if any(
        mount.get("Type") == "volume"
        for mount in payload.get("Mounts", [])
        if mount.get("Destination") == POSTGRES_DATA_DIR
    ):
        raise BaselineError(
            "A persistent Docker volume is mounted as PostgreSQL storage"
        )
    networks = payload.get("NetworkSettings", {}).get("Networks") or {}
    if target.network_name not in networks:
        raise BaselineError(
            "Container is not attached to its generated baseline network"
        )

    network_result = _docker(["network", "inspect", target.network_name])
    network_payload = json.loads(network_result.stdout)[0]
    network_labels = network_payload.get("Labels") or {}
    if network_labels.get(RESOURCE_LABEL) != target.identity:
        raise BaselineError("Network baseline identity label does not match")


def _wait_for_postgres(target: DatabaseTarget) -> None:
    deadline = time.monotonic() + 60
    last_error = "not ready"
    while time.monotonic() < deadline:
        try:
            with psycopg2.connect(**target.connection_kwargs()):
                return
        except psycopg2.Error as exc:
            last_error = exc.__class__.__name__
            time.sleep(1)
    raise BaselineError(f"Disposable PostgreSQL did not become ready ({last_error})")


def _prepare_timezone_data(target: DatabaseTarget, directory: Path) -> Path:
    timezone_dir = directory / "zoneinfo"
    timezone_dir.mkdir()
    for destination_name, source_name in TIMEZONE_FILES.items():
        destination = timezone_dir / Path(destination_name)
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = _docker(
            [
                "cp",
                f"{target.container_name}:/usr/share/zoneinfo/{source_name}",
                str(destination.relative_to(directory)),
            ],
            check=False,
            cwd=directory,
        )
        if result.returncode != 0 or not destination.is_file():
            detail = (result.stderr or result.stdout).strip()
            raise BaselineError(
                "Could not prepare disposable IANA timezone data for "
                f"{destination_name}" + (f": {detail}" if detail else "")
            )
    return timezone_dir


def _verify_empty_postgres(target: DatabaseTarget) -> str:
    with psycopg2.connect(**target.connection_kwargs()) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT current_database(), current_user,
                       current_setting('server_version_num')::integer
                """
            )
            database, username, version_num = cursor.fetchone()
            cursor.execute(
                """
                SELECT count(*)
                FROM pg_class AS c
                JOIN pg_namespace AS n ON n.oid = c.relnamespace
                WHERE n.nspname NOT IN ('pg_catalog', 'information_schema')
                  AND n.nspname !~ '^pg_toast'
                  AND c.relkind IN ('r', 'p', 'v', 'm', 'S', 'f')
                """
            )
            relation_count = cursor.fetchone()[0]
    if database != target.database or username != target.username:
        raise BaselineError(
            "Connected database identity does not match the generated target"
        )
    if version_num // 10000 != 16:
        raise BaselineError(f"PostgreSQL 16 required; server reported {version_num}")
    if relation_count != 0:
        raise BaselineError(
            f"Baseline database is not empty before migrations ({relation_count} relations)"
        )
    return str(version_num)


def _verify_alembic_head(target: DatabaseTarget, alembic_ini: Path) -> str:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    config = Config(str(alembic_ini))
    expected_heads = ScriptDirectory.from_config(config).get_heads()
    if len(expected_heads) != 1:
        raise BaselineError(f"Expected one Alembic head, found {expected_heads}")
    with psycopg2.connect(**target.connection_kwargs()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT version_num FROM alembic_version")
            actual_heads = [row[0] for row in cursor.fetchall()]
    if actual_heads != expected_heads:
        raise BaselineError(
            f"Database Alembic head {actual_heads} does not match repository {expected_heads}"
        )
    return actual_heads[0]


def _verify_pytest_summary(output: str) -> None:
    summary_lines = [
        line.strip()
        for line in output.splitlines()
        if re.search(r"\bpassed\b.*\bin\s+\d", line)
    ]
    if len(summary_lines) != 1:
        raise BaselineError("Could not identify one unambiguous pytest summary line")
    summary = summary_lines[0]
    passed_match = re.search(r"(?<!\d)(\d+)\s+passed\b", summary)
    if not passed_match or int(passed_match.group(1)) != EXPECTED_TEST_COUNT:
        raise BaselineError(
            f"Expected exactly {EXPECTED_TEST_COUNT} passed tests; got: {summary}"
        )
    forbidden = ("skipped", "xfailed", "xpassed")
    if any(re.search(rf"(?<!\d)[1-9]\d*\s+{word}\b", summary) for word in forbidden):
        raise BaselineError(f"Skips or xfails are forbidden in the baseline: {summary}")
    allowed = re.fullmatch(
        rf"{EXPECTED_TEST_COUNT}\s+passed"
        rf"(?:,\s+\d+\s+warnings?)?"
        rf"\s+in\s+\d+(?:\.\d+)?s",
        summary,
    )
    if not allowed:
        raise BaselineError(f"Unexpected pytest result categories: {summary}")
    print(f"Pytest contract verified: {summary}")
    print("Skip/xfail contract verified: skipped=0, xfailed=0, xpassed=0")


def _type_name(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value)).strip().lower()


def _column_contract(column: Any) -> dict[str, Any]:
    return {
        "name": column.name,
        "type": _type_name(column.type),
        "nullable": bool(column.nullable),
        "primary_key": bool(column.primary_key),
    }


def _table_contract(table: Any) -> dict[str, Any]:
    return {
        "schema": table.schema,
        "table": table.name,
        "columns": [_column_contract(column) for column in table.columns],
    }


def _index_contract(index: Any) -> dict[str, Any]:
    return {
        "schema": index.table.schema,
        "table": index.table.name,
        "index": index.name,
        "columns": [
            getattr(expression, "name", str(expression))
            for expression in index.expressions
        ],
        "unique": bool(index.unique),
    }


def _flatten_diffs(diffs: Iterable[Any]) -> Iterable[tuple[Any, ...]]:
    for diff in diffs:
        if isinstance(diff, (list, tuple)) and diff and not isinstance(diff[0], str):
            yield from _flatten_diffs(diff)
        elif isinstance(diff, tuple) and diff and isinstance(diff[0], str):
            yield diff
        else:
            raise BaselineError(
                f"Unclassifiable Alembic drift object: {type(diff).__name__}"
            )


def _canonicalize_diff(diff: tuple[Any, ...]) -> dict[str, Any]:
    operation = diff[0]
    if operation in {"add_table", "remove_table"}:
        return {"operation": operation, **_table_contract(diff[1])}
    if operation in {"add_index", "remove_index"}:
        return {"operation": operation, **_index_contract(diff[1])}
    if operation in {"add_column", "remove_column"}:
        schema, table, column = diff[1], diff[2], diff[3]
        return {
            "operation": operation,
            "schema": schema,
            "table": table,
            "column": _column_contract(column),
        }
    if operation == "modify_type":
        schema, table, column = diff[1], diff[2], diff[3]
        return {
            "operation": operation,
            "schema": schema,
            "table": table,
            "column": column,
            "from": _type_name(diff[-2]),
            "to": _type_name(diff[-1]),
        }
    raise BaselineError(f"Unclassifiable Alembic drift operation: {operation}")


def _actual_drift(target: DatabaseTarget) -> list[dict[str, Any]]:
    from alembic.autogenerate import compare_metadata
    from alembic.migration import MigrationContext
    from sqlalchemy import create_engine

    from app.models import Base

    engine = create_engine(target.sqlalchemy_url)
    try:
        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            raw_diffs = compare_metadata(context, Base.metadata)
    finally:
        engine.dispose()
    canonical = [_canonicalize_diff(diff) for diff in _flatten_diffs(raw_diffs)]
    return sorted(canonical, key=lambda entry: json.dumps(entry, sort_keys=True))


def _verify_known_drift(
    target: DatabaseTarget, check_result: subprocess.CompletedProcess[str]
) -> None:
    output = check_result.stdout or ""
    if check_result.returncode == 0:
        raise BaselineError(
            "alembic check unexpectedly passed; Issue #15 baseline contract must be updated"
        )
    if "New upgrade operations detected" not in output:
        raise BaselineError(
            "alembic check failed for an unrecognized reason; refusing to accept the failure"
        )
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    if manifest.get("issue") != "https://github.com/smytsyk-beep/a_daily/issues/15":
        raise BaselineError("Known-drift manifest is not linked to GitHub Issue #15")
    expected = sorted(
        manifest.get("expected_drift", []),
        key=lambda entry: json.dumps(entry, sort_keys=True),
    )
    actual = _actual_drift(target)
    if actual != expected:
        print(
            "Expected drift contract:", json.dumps(expected, indent=2, sort_keys=True)
        )
        print("Actual drift contract:", json.dumps(actual, indent=2, sort_keys=True))
        raise BaselineError("Alembic drift differs from the audited Issue #15 baseline")
    print(f"Known drift contract matched exactly ({len(actual)} entries)")
    print("Expected failure owner: https://github.com/smytsyk-beep/a_daily/issues/15")


def _resource_exists(kind: str, name: str) -> bool:
    return _docker([kind, "inspect", name], check=False).returncode == 0


def _cleanup(target: DatabaseTarget) -> None:
    cleanup_errors: list[str] = []
    _docker(["rm", "--force", target.container_name], check=False)
    _docker(["network", "rm", target.network_name], check=False)
    if _resource_exists("container", target.container_name):
        cleanup_errors.append(f"container {target.container_name} still exists")
    if _resource_exists("network", target.network_name):
        cleanup_errors.append(f"network {target.network_name} still exists")
    if cleanup_errors:
        raise BaselineError("Cleanup verification failed: " + "; ".join(cleanup_errors))
    print(
        "Cleanup verified: disposable container, network, and tmpfs data removed "
        f"(identity {target.identity})"
    )


def _handle_signal(signum: int, _frame: Any) -> None:
    raise BaselineInterrupted(f"Interrupted by signal {signum}")


def run_baseline() -> None:
    for signal_name in ("SIGINT", "SIGTERM", "SIGBREAK"):
        if hasattr(signal, signal_name):
            signal.signal(getattr(signal, signal_name), _handle_signal)

    target = _make_target()
    base_env = _sanitized_base_env()
    failure: BaseException | None = None
    cleanup_required = False

    with tempfile.TemporaryDirectory(prefix="astrodaily-baseline-") as temp_name:
        temp_dir = Path(temp_name)
        alembic_ini = _write_isolated_alembic_config(temp_dir)
        base_env["ALEMBIC_INI"] = str(alembic_ini)

        try:
            _print_step(1, "Run pre-commit against all files")
            _run(
                [
                    sys.executable,
                    "-m",
                    "pre_commit",
                    "run",
                    "--all-files",
                    "--show-diff-on-failure",
                ],
                cwd=REPO_ROOT,
                env=base_env,
                display="python -m pre_commit run --all-files --show-diff-on-failure",
            )

            _print_step(2, "Create isolated PostgreSQL 16")
            _check_docker_available()
            cleanup_required = True
            target = _create_postgres(target)
            _verify_docker_identity(target)
            _wait_for_postgres(target)
            timezone_dir = _prepare_timezone_data(target, temp_dir)
            print(
                "Disposable target ready: "
                f"identity={target.identity}, host={target.host}, port={target.port}, "
                "storage=tmpfs"
            )

            _print_step(3, "Verify PostgreSQL version and empty baseline database")
            version_num = _verify_empty_postgres(target)
            print(
                f"PostgreSQL version verified: server_version_num={version_num}; "
                "baseline relations=0"
            )
            database_env = _database_env(base_env, target)
            database_env["PYTHONTZPATH"] = str(timezone_dir)

            _print_step(4, "Run fresh Alembic upgrade to head")
            _run(
                [
                    sys.executable,
                    "-m",
                    "alembic",
                    "-c",
                    str(alembic_ini),
                    "upgrade",
                    "head",
                ],
                cwd=temp_dir,
                env=database_env,
                display="python -m alembic -c <isolated-config> upgrade head",
            )

            _print_step(5, "Verify current Alembic head")
            head = _verify_alembic_head(target, alembic_ini)
            print(f"Alembic head verified: {head}")

            _print_step(6, "Run the audited pytest suite")
            pytest_result = _run(
                [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    str(REPO_ROOT / "tests"),
                    "-p",
                    "no:cacheprovider",
                ],
                cwd=temp_dir,
                env=database_env,
                display="python -m pytest -q tests -p no:cacheprovider",
            )

            _print_step(
                7,
                f"Verify exact pytest result: {EXPECTED_TEST_COUNT} passed",
            )
            _verify_pytest_summary(pytest_result.stdout or "")

            _print_step(8, "Verify no skips or xfails")
            print("No skip/xfail categories were present in the exact pytest summary")

            _print_step(9, "Run real Alembic check")
            check_result = _run(
                [
                    sys.executable,
                    "-m",
                    "alembic",
                    "-c",
                    str(alembic_ini),
                    "check",
                ],
                cwd=temp_dir,
                env=database_env,
                display="python -m alembic -c <isolated-config> check",
                check=False,
            )

            _print_step(10, "Validate the audited known drift")
            _verify_known_drift(target, check_result)

            _print_step(11, "Run git diff whitespace check")
            _run(
                ["git", "diff", "--check"],
                cwd=REPO_ROOT,
                env=base_env,
                display="git diff --check",
            )
        except BaseException as exc:
            failure = exc
        finally:
            _print_step(12, "Cleanup isolated PostgreSQL resources")
            try:
                if cleanup_required:
                    _cleanup(target)
                else:
                    print(
                        "Cleanup verified: no disposable Docker resources were created"
                    )
            except BaseException as cleanup_exc:
                if failure is None:
                    failure = cleanup_exc
                else:
                    print(f"Additional cleanup failure: {cleanup_exc}", file=sys.stderr)

        if failure is not None:
            raise failure

    print("\nBaseline verification passed.", flush=True)


def main() -> int:
    try:
        run_baseline()
    except BaselineInterrupted as exc:
        print(f"\nBASELINE INTERRUPTED: {exc}", file=sys.stderr)
        return 130
    except (BaselineError, subprocess.TimeoutExpired, psycopg2.Error) as exc:
        print(f"\nBASELINE FAILED: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

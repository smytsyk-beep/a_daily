# Audited baseline verification

Issue [#33](https://github.com/smytsyk-beep/a_daily/issues/33) defines one
verification path for local development and GitHub Actions. It reproduces the
audited test and migration baseline without using a developer, staging, or
production database.

The historical audited baseline remains `100 passed`. Issue
[#35](https://github.com/smytsyk-beep/a_daily/issues/35) increased the exact
contract to `156 passed`. Issue
[#36](https://github.com/smytsyk-beep/a_daily/issues/36) adds production route,
health, environment, and startup-isolation coverage and increased the exact
contract to `186 passed`. Issue
[#37](https://github.com/smytsyk-beep/a_daily/issues/37) adds trusted-host,
safe-error, correlation-ID, and expanded production exposure coverage and
increased the exact contract to `226 passed`. Issue
[#38](https://github.com/smytsyk-beep/a_daily/issues/38) adds canonical plan,
digest-policy, compatibility, and time-aware entitlement coverage, so the
current exact regression-suite contract is `299 passed`.

## Prerequisites

- Python 3.11 with `requirements.txt` installed;
- `pre-commit` installed in the same Python environment;
- Docker with a running Linux-container daemon;
- permission to create and remove Docker containers and networks;
- a clean enough checkout for `pre-commit` and `git diff --check` to pass.

Install the Python dependencies:

```text
python -m pip install -r requirements.txt
python -m pip install pre-commit
```

Do not set a test `DATABASE_URL`. The runner ignores any ambient
`DATABASE_URL`, database password, token, secret, and API-key variables and
constructs its own disposable target.

## Canonical command

Run from the repository root on Windows, macOS, or Linux:

```text
python scripts/verify_baseline.py
```

GitHub Actions uses the same command in the `Verify audited baseline` step of
`.github/workflows/ci.yml`.

## Verification order

The runner performs this exact sequence:

1. `pre-commit run --all-files --show-diff-on-failure`;
2. create a uniquely named PostgreSQL 16 container and Docker network;
3. verify the generated identity, PostgreSQL major version, `tmpfs` storage,
   and an empty database;
4. run a fresh `alembic upgrade head`;
5. compare the database revision with the single repository Alembic head;
6. run `pytest -q tests -p no:cacheprovider`;
7. require exactly `299 passed`;
8. reject any skip, xfail, or xpass result;
9. run the real `alembic check` command;
10. compare its semantic drift with `scripts/baseline_known_drift.json`;
11. run `git diff --check`;
12. remove and verify removal of the container, network, `tmpfs` data, copied
    timezone data, and other temporary files.

Cleanup runs after success, command failure, and interruption. A cleanup
failure makes the overall command fail.

## Database isolation and safety

Each run generates a new baseline identity used in the container, network,
database, role, and Docker labels. PostgreSQL binds only to a random port on
`127.0.0.1`; its data directory is `tmpfs`, and no Docker volume is created.
The runner verifies the container image, labels, network membership, storage
type, database/role identity, PostgreSQL 16 server version, and zero
non-system relations before migration.

Application and migration subprocesses receive only the generated test DSN.
They run with an isolated temporary Alembic configuration and safe test
settings. Application commands use a temporary working directory without the
repository `.env`. IANA timezone data is copied from the disposable container
to that temporary directory so Windows and Linux use the same isolated test
path.

The runner never executes destructive SQL against an external DSN and never
falls back to another database when Docker is unavailable.

## Expected output

Names, IDs, and ports vary. Credentials and the complete DSN are never
printed. A shortened example is:

```text
[2/12] Create isolated PostgreSQL 16
Disposable target ready: identity=issue33-<random>, host=127.0.0.1,
port=<random>, storage=tmpfs
[3/12] Verify PostgreSQL version and empty baseline database
PostgreSQL version verified: server_version_num=1600xx; baseline relations=0
[5/12] Verify current Alembic head
Alembic head verified: a1b2c3d4e5f6
[7/12] Verify exact pytest result: 299 passed
Pytest contract verified: 299 passed in <seconds>s
[10/12] Validate the audited known drift
Known drift contract matched exactly (11 entries)
[12/12] Cleanup isolated PostgreSQL resources
Cleanup verified: disposable container, network, and tmpfs data removed
Baseline verification passed.
```

Warnings may be reported by pytest, but the current result contract remains
exactly 299 passed with zero skips, xfails, and xpasses.

## Known Alembic drift

Until tracking Issue
[#15](https://github.com/smytsyk-beep/a_daily/issues/15) is completed,
`alembic check` must fail with the exact 11-entry semantic contract stored in
`scripts/baseline_known_drift.json`. The runner accepts only the known removed
table/index, added index, and type-change entries.

The baseline fails when:

- `alembic check` unexpectedly succeeds;
- the command fails for a reason other than detected upgrade operations;
- an expected drift entry disappears or changes;
- a new drift entry appears;
- an operation cannot be classified.

After Issue #15 repairs the schema, this expected-failure contract must be
removed or replaced by a clean `alembic check` gate in that issue's scope. Do
not use `alembic check || true`.

## Troubleshooting

- **Docker daemon unavailable:** start Docker and rerun. Do not substitute a
  development, shared, staging, or production database.
- **PostgreSQL is not empty or not version 16:** let the runner clean up and
  rerun. Do not point it at another DSN.
- **Pre-commit modifies files:** inspect the modifications, stage or revert
  them intentionally, then rerun.
- **Test count differs from 299:** stop and investigate the regression-suite
  change;
  do not add skips or alter test selection.
- **Known drift differs:** compare the semantic output with Issue #15. Do not
  update the manifest merely to make CI green.
- **Cleanup fails:** use the printed generated identity to inspect only that
  labeled resource. Never run `docker compose down -v` against the developer
  environment.

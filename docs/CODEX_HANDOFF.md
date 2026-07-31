# AstroDaily Codex Handoff

## Baseline

- Audited commit: `60b6468401253a8484e8ae6a5734259d60e26639`
- Audited branch: `preprod-audit`
- Audit date: `2026-07-30`
- Production decision: `NO-GO`
- Baseline tests: `100 passed in 14.88s` on isolated PostgreSQL 16
- Fresh `alembic upgrade head`: `passed` on a clean database
- `alembic check`: currently `failed` due to ORM/migration schema drift
- Scheduled delivery: `disabled`

## Current work

- Current working branch: `docs/32-governance-handoff`
- Worktree: `dirty` — Issue #32 governance files and pre-existing unrelated
  local changes are uncommitted; unrelated changes remain excluded
- Active milestone:
  [Wave A — Mandatory Foundation (Pilot Gate)](https://github.com/smytsyk-beep/a_daily/milestone/1)
- Current tracking issue:
  [#12 — Baseline, governance and architecture decisions](https://github.com/smytsyk-beep/a_daily/issues/12)
- Current implementation issue:
  [#32 — Establish repository governance and Codex handoff](https://github.com/smytsyk-beep/a_daily/issues/32)
- Current PR: `none`
- Application code changed for Issue #32: `no`

## Completed issues

- None.

## Architecture invariants

- Default plan without entitlement is `demo`.
- The only public pilot routes are `POST /telegram/webhook` and `GET /health`.
- Calendar is disabled for the first pilot.
- AstroDaily is a channel-agnostic modular monolith.
- Telegram is a transport adapter; domain/application code is channel-neutral.
- PostgreSQL transactional outbox is the canonical queue.
- The first pilot uses one web instance, one worker, and managed PostgreSQL.
- Redis, Kubernetes, and microservices are not used.
- Scheduled delivery remains disabled until separately approved.
- Historical Alembic migrations must not be edited.
- Schema corrections use new forward migrations.
- Manual plans are assigned only through audit-logged admin CLI.

## Required reading order

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. The current GitHub implementation issue
4. Its parent tracking issue
5. `docs/Correction_plan_AstroDaily_2026-07-30.md`
6. `docs/preprod_code_audit.md` when the issue references an audit finding

The current implementation issue is authoritative. Update this handoff when
selecting or completing an issue. Update only the Correction plan
`Implementation status` section when an issue is selected, completed, or
blocked, or when the release decision changes. Detailed implementation state
belongs in GitHub issues and pull requests.

## Required verification

Run with an explicit test `DATABASE_URL` against isolated PostgreSQL 16:

```text
pre-commit run --all-files --show-diff-on-failure
alembic upgrade head
alembic check
pytest -q tests
git diff --check
```

`alembic check` is expected to fail until the schema-drift issue is completed;
all other baseline checks must not regress.

## Links

- [Pre-production code audit](preprod_code_audit.md)
- [Correction plan](Correction_plan_AstroDaily_2026-07-30.md)
- [Current tracking issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Current implementation issue #32](https://github.com/smytsyk-beep/a_daily/issues/32)

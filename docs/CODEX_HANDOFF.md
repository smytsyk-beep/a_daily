# AstroDaily Codex Handoff

## Baseline

- Audited commit: `60b6468401253a8484e8ae6a5734259d60e26639`
- Audited branch: `preprod-audit`
- Audit date: `2026-07-30`
- Production decision: `NO-GO`
- Baseline tests: `100 passed in 14.88s` on isolated PostgreSQL 16
- Fresh `alembic upgrade head`: `passed` on a clean database
- `alembic check`: currently `failed` due to ORM/migration schema drift
- Canonical baseline command: `python scripts/verify_baseline.py`
- Scheduled delivery: `disabled`

## Current work

- Approved remediation base branch: `main`
- Current working branch: `fix/35-fail-fast-production-settings`
- Worktree: clean; Issue #35 commits pushed to PR #61
- Active milestone:
  [Wave A — Mandatory Foundation (Pilot Gate)](https://github.com/smytsyk-beep/a_daily/milestone/1)
- Current tracking issue:
  [#13 — Enforce the pilot production API boundary](https://github.com/smytsyk-beep/a_daily/issues/13)
- Current implementation issue:
  [#35 — Add fail-fast production settings and secret validation](https://github.com/smytsyk-beep/a_daily/issues/35)
- Current PR:
  [#61 — Add fail-fast production settings and secret validation](https://github.com/smytsyk-beep/a_daily/pull/61)
- Settings validation status: `implemented; locally and CI verified`
- ADR status: four accepted decision records and their canonical index merged
  via PR #59
- Baseline verification: `passed` locally for Issue #35 on Windows/Python 3.13
  on `2026-07-31`; canonical GitHub Actions Python 3.11 baseline passed on
  PR #61
- Disposable database: PostgreSQL `160011`, empty before migrations
- Fresh migration result: `passed`, head `a1b2c3d4e5f6`
- Current regression suite: `156 passed, 128 warnings`; skips/xfails/xpasses
  all zero (historical audited baseline remains `100 passed`)
- Expected Alembic drift: real `alembic check` failed and matched all 11
  Issue #15 manifest entries exactly
- Cleanup: generated container, network, `tmpfs`, timezone data, and temporary
  configuration removed and verified
- Production settings/startup tests: invalid production configuration blocks
  canonical app import; valid configuration imports without DB/provider access
- Route inventory: unchanged by Issue #35; production route filtering remains
  owned by Issues #36 and #37
- Latest merged PR:
  [#59 — Record trust-boundary, modular-monolith, outbox, and migration ADRs](https://github.com/smytsyk-beep/a_daily/pull/59)
- Historical migration code changed for Issue #35: `no`

## Completed issues

- [#32 — Establish repository governance and Codex handoff](https://github.com/smytsyk-beep/a_daily/issues/32)
  via [PR #55](https://github.com/smytsyk-beep/a_daily/pull/55), merged
  `2026-07-31`
- [#33 — Make the audited test and migration baseline reproducible](https://github.com/smytsyk-beep/a_daily/issues/33)
  via [PR #57](https://github.com/smytsyk-beep/a_daily/pull/57), merged
  `2026-07-31`
- [#34 — Record trust-boundary, modular-monolith, outbox, and migration ADRs](https://github.com/smytsyk-beep/a_daily/issues/34)
  via [PR #59](https://github.com/smytsyk-beep/a_daily/pull/59), merged
  `2026-07-31`

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

Run the canonical isolated PostgreSQL 16 baseline:

```text
python scripts/verify_baseline.py
```

The runner requires exactly 100 passing tests with no skips/xfails, a fresh
upgrade to `a1b2c3d4e5f6`, and an exact match to the expected 11-entry Alembic
drift owned by Issue #15. It verifies disposable resource cleanup.

## Links

- [Pre-production code audit](preprod_code_audit.md)
- [Correction plan](Correction_plan_AstroDaily_2026-07-30.md)
- [Current tracking issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Known schema drift tracking issue #15](https://github.com/smytsyk-beep/a_daily/issues/15)
- [Baseline verification guide](baseline_verification.md)
- [Application configuration contract](configuration.md)
- [Architecture Decision Record index](adr/README.md)
- [Completed implementation issue #32](https://github.com/smytsyk-beep/a_daily/issues/32)
- [Completed implementation issue #33](https://github.com/smytsyk-beep/a_daily/issues/33)
- [Completed implementation issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Merged PR #57](https://github.com/smytsyk-beep/a_daily/pull/57)
- [Merged PR #59](https://github.com/smytsyk-beep/a_daily/pull/59)

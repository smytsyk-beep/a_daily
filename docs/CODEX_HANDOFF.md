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
- Current working branch: `fix/37-trusted-host-safe-errors`
- Worktree: Issue #37 commits pushed to draft PR #63
- Active milestone:
  [Wave A — Mandatory Foundation (Pilot Gate)](https://github.com/smytsyk-beep/a_daily/milestone/1)
- Current tracking issue:
  [#13 — Enforce the pilot production API boundary](https://github.com/smytsyk-beep/a_daily/issues/13)
- Current implementation issue:
  [#37 — Add trusted-host, safe-error, and production route-exposure tests](https://github.com/smytsyk-beep/a_daily/issues/37)
- Current PR:
  [#63 — Enforce trusted hosts and safe public errors](https://github.com/smytsyk-beep/a_daily/pull/63)
- Trusted-host/safe-error status: `implemented and locally verified; draft PR #63 open`
- Production route-boundary status: `completed via PR #62`
- Settings validation status: `completed via PR #61`
- ADR status: four accepted decision records and their canonical index merged
  via PR #59
- Baseline verification: `passed` locally for Issue #37 on Windows/Python 3.13
  on `2026-07-31`; latest canonical GitHub Actions Python 3.11 baseline passed
  on PR #62
- Disposable database: PostgreSQL `160011`, empty before migrations
- Fresh migration result: `passed`, head `a1b2c3d4e5f6`
- Current regression suite: `226 passed, 128 warnings`; skips/xfails/xpasses
  all zero (historical audited baseline remains `100 passed`)
- Expected Alembic drift: real `alembic check` failed and matched all 11
  Issue #15 manifest entries exactly
- Cleanup: generated container, network, `tmpfs`, timezone data, and temporary
  configuration removed and verified
- Production settings/startup tests: invalid configuration blocks canonical app
  import; valid production assembly performs no DB/provider I/O
- Production route inventory: exactly `GET /health` and
  `POST /telegram/webhook`; private route modules are not imported
- Health contract: `{"status": "ok"}` in every environment
- Production middleware order: correlation ID, trusted-host enforcement,
  FastAPI routing; safe errors use one stable JSON envelope
- Latest merged PR:
  [#62 — Enforce the pilot production router boundary](https://github.com/smytsyk-beep/a_daily/pull/62)
- Historical migration code changed for Issue #37: `no`

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
- [#35 — Add fail-fast production settings and secret validation](https://github.com/smytsyk-beep/a_daily/issues/35)
  via [PR #61](https://github.com/smytsyk-beep/a_daily/pull/61), merged
  `2026-07-31`
- [#36 — Register only health and Telegram webhook on the public production app](https://github.com/smytsyk-beep/a_daily/issues/36)
  via [PR #62](https://github.com/smytsyk-beep/a_daily/pull/62), merged
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

The runner requires exactly 186 passing tests with no skips/xfails, a fresh
upgrade to `a1b2c3d4e5f6`, and an exact match to the expected 11-entry Alembic
drift owned by Issue #15. It verifies disposable resource cleanup.

## Links

- [Pre-production code audit](preprod_code_audit.md)
- [Correction plan](Correction_plan_AstroDaily_2026-07-30.md)
- [Current tracking issue #13](https://github.com/smytsyk-beep/a_daily/issues/13)
- [Known schema drift tracking issue #15](https://github.com/smytsyk-beep/a_daily/issues/15)
- [Baseline verification guide](baseline_verification.md)
- [Application configuration contract](configuration.md)
- [Architecture Decision Record index](adr/README.md)
- [Completed implementation issue #32](https://github.com/smytsyk-beep/a_daily/issues/32)
- [Completed implementation issue #33](https://github.com/smytsyk-beep/a_daily/issues/33)
- [Completed implementation issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Completed implementation issue #35](https://github.com/smytsyk-beep/a_daily/issues/35)
- [Completed implementation issue #36](https://github.com/smytsyk-beep/a_daily/issues/36)
- [Merged PR #57](https://github.com/smytsyk-beep/a_daily/pull/57)
- [Merged PR #59](https://github.com/smytsyk-beep/a_daily/pull/59)
- [Merged PR #61](https://github.com/smytsyk-beep/a_daily/pull/61)
- [Merged PR #62](https://github.com/smytsyk-beep/a_daily/pull/62)

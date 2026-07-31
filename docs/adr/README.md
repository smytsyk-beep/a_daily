# AstroDaily Architecture Decision Records

This directory is the canonical index for durable AstroDaily architecture
decisions. ADRs record decisions that implementation pull requests must follow;
they do not replace issue-specific scope, acceptance criteria, or runbooks.

## Convention

- ADRs use four-digit, monotonically increasing numbers and descriptive
  filenames: `NNNN-short-title.md`.
- The initial status is `Accepted`. Other valid lifecycle statuses are
  `Proposed`, `Deprecated`, and `Superseded`.
- An accepted ADR is immutable as a decision record. Editorial corrections may
  clarify links or spelling, but a changed decision requires a new ADR. The new
  ADR marks the old ADR `Superseded` and links both records.
- Pilot requirements are separated from post-pilot evolution so deferred
  capabilities cannot be exposed early.
- Every implementation PR affected by an ADR must cite it and provide the
  verification evidence named in that ADR.

## Accepted decisions

| ADR | Status | Decision | Pilot scope | Post-pilot boundary |
|---|---|---|---|---|
| [ADR-0001](0001-production-http-trust-boundary.md) | Accepted | Expose only the health check and authenticated Telegram webhook as public pilot routes. | `GET /health` and `POST /telegram/webhook`; all other HTTP surfaces absent from public production. | Internal service and public PWA APIs require separate trust models and decisions. |
| [ADR-0002](0002-channel-agnostic-modular-monolith.md) | Accepted | Keep one channel-agnostic modular monolith with transport adapters. | One codebase, one public web service, one worker, managed scheduler, and managed PostgreSQL in one region. | New channels reuse application use cases; service extraction requires a new ADR and demonstrated need. |
| [ADR-0003](0003-postgresql-transactional-outbox.md) | Accepted | Use PostgreSQL as the source of truth, durable update ledger, transactional outbox, and idempotency store. | One web instance and one worker with at-least-once processing and idempotent business side effects; no broker. | A broker or Redis requires a new ADR and measured need; Redis is not the canonical queue. |
| [ADR-0004](0004-forward-only-production-migrations.md) | Accepted | Keep production migration history append-only and roll applications back by image plus forward fix. | One Alembic head, corrective forward migrations, one approved image digest, and migration-before-deploy gates. | Incompatible evolution uses expand/contract; production does not depend on destructive downgrades. |

## Governance and source decisions

- Implementation issue:
  [#34 — Record architecture and migration ADRs](https://github.com/smytsyk-beep/a_daily/issues/34)
- Parent tracking issue:
  [#12 — Baseline, governance and architecture decisions](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Correction plan](../Correction_plan_AstroDaily_2026-07-30.md)
- [Audited baseline and pre-production audit reference](../CODEX_HANDOFF.md#baseline)

The source audit path referenced by repository governance is
`docs/preprod_code_audit.md`. It is not tracked on the approved `main` base as
of this ADR set; the accepted decisions above use the audit findings reconciled
into the Correction plan and GitHub backlog.

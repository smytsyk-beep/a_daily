# AstroDaily Engineering Rules

These rules apply to the entire repository.

## Required context

Before starting an implementation issue, read in this order:

1. `AGENTS.md`
2. `docs/CODEX_HANDOFF.md`
3. The current GitHub issue
4. The parent tracking issue
5. `docs/Correction_plan_AstroDaily_2026-07-30.md`
6. `docs/preprod_code_audit.md` when the issue references an audit finding

The current GitHub issue is the authoritative implementation scope. Do not
implement adjacent backlog items in the same pull request.

## Delivery discipline

- One implementation issue produces one focused pull request.
- Preserve unrelated user changes and do not edit unrelated files.
- Every behavioral change requires automated tests.
- Update `docs/CODEX_HANDOFF.md` when selecting or completing an issue.
- Keep the handoff concise: current baseline, active work, completed issue
  numbers, current invariants, verification commands, and links only.
- Update only the Correction plan `Implementation status` section when an issue
  is selected, completed, or blocked, or when the release decision changes.
  Keep detailed implementation state in GitHub issues and pull requests.
- Do not mark work complete until its acceptance criteria and required tests
  pass.
- Application code must not be changed while working on planning-only or
  documentation-only issues.

## Architecture invariants

- AstroDaily is a channel-agnostic modular monolith, not a microservice system.
- Telegram is a transport adapter. Domain and application code must not import
  Telegram, FastAPI, WhatsApp, Viber, or provider HTTP clients.
- Channel-neutral use cases and messaging contracts are shared by all
  transports.
- The first pilot uses one public web service, one background worker, a managed
  scheduler, and managed PostgreSQL in one region.
- PostgreSQL transactional outbox is the canonical queue.
- Do not add Redis, Celery, Kubernetes, or microservices for the first pilot.
- Redis may be reconsidered only for shared cache and distributed rate limiting
  after more than one web instance is approved.

## Production trust boundary

- The only public pilot routes are `POST /telegram/webhook` and `GET /health`.
- Calendar is disabled for the first pilot.
- Public web/mobile `/api/v1` is post-pilot and must not be exposed early.
- User, admin, metrics, docs, preview, events, and internal endpoints must be
  disabled in production or protected by service authentication and a private
  network policy.
- Do not create a public admin API.
- Manual entitlement changes go through an audit-logged admin CLI, never a
  public endpoint or an operational raw-SQL procedure.
- Never commit, print, or log secrets, birth data, coordinates, raw provider
  payloads, or full user preferences.

## Plans and delivery

- The default plan without an effective entitlement is `demo`.
- The canonical digest caps are `demo=short/2`, `daily=medium/3`, and
  `full|internal=long/6`, with shorter user preferences preserved.
- Every feature gate must use one canonical, time-aware plan service.
- Scheduled delivery remains disabled until its dedicated release gate passes.
- State commands write the desired value; they must not toggle state.
- External messaging is at-least-once; business side effects must be
  idempotent.

## Database and migrations

- PostgreSQL 16 is the target database.
- Do not edit historical Alembic revisions.
- Correct schema defects with new forward migrations.
- Production rollback uses the previous image plus a forward-fix migration; it
  does not rely on destructive schema downgrade.
- Every new migration needs upgrade coverage, constraint/data verification,
  and a downgrade suitable for development and tests.
- Run `alembic check` after ORM or schema changes.
- The canonical ORM model name is `EventFeedback` (singular). Do not introduce
  an `EventsFeedback` model or a duplicate feedback model.
- Use aware UTC datetimes and explicit timezone conversion.

## Required verification

Run the checks relevant to the issue. The default full set is:

```bash
pre-commit run --all-files --show-diff-on-failure
alembic upgrade head
alembic check
pytest -q tests
git diff --check
```

Database commands require an isolated PostgreSQL 16 database and an explicit
`DATABASE_URL`. Do not run migration or data-mutating tests against production.

## Definition of Done

An implementation issue is done only when all of the following are true:

- Its Context, Scope, Acceptance criteria, Required tests, Dependencies, Risk
  level, and Parent tracking issue are current and contain no unresolved TBDs.
- Every acceptance criterion is satisfied with evidence in the pull request.
- Required unit, integration, migration, security, or container tests were
  added or updated and pass.
- The relevant default verification commands pass. A pre-existing expected
  failure must be linked to its owning issue and must not get worse.
- The change contains no unrelated refactor, formatting churn, generated
  secrets, personal data, or debug artifacts.
- Database work uses a new forward migration, verifies migrated data and
  constraints, and leaves `alembic check` clean for the affected metadata.
- Security-sensitive work documents trust-boundary and failure-mode effects.
- User-facing behavior is localized where EN/ES/RU support applies.
- Operational or interface changes update the relevant runbook, ADR, or
  contract documentation.
- `docs/CODEX_HANDOFF.md` identifies the issue while active and records it under
  completed issues after merge.

A pull request is done only when all of the following are true:

- It implements exactly one implementation issue and links both that issue and
  its parent tracking issue.
- Its description includes Summary, Scope, Risk, Test evidence, migration or
  rollback notes when applicable, and a statement of out-of-scope work.
- All required CI checks pass and `git diff --check` is clean.
- Review comments and security findings are resolved.
- The branch is current with its approved remediation base without destructive
  history rewriting.
- The parent tracking checklist and handoff are updated after merge.
- The implementation issue is closed only after the merge commit is present on
  the approved base branch.

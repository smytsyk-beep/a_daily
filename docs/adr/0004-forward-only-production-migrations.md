# ADR-0004: Forward-Only Production Migrations

- Status: Accepted
- Date: 2026-07-31
- Decision scope: Pilot / Post-pilot boundaries

## Context

The audit found a clean upgrade but also ORM/migration drift, duplicate table
contracts, and a historical downgrade that fails after realistic data exists.
Editing old revisions would make environments with the same revision identifier
represent different schemas. Depending on destructive downgrade or automatic
database restore for an application rollback would put durable user and outbox
state at unnecessary risk.

## Decision

Production Alembic history is append-only. Historical revisions are not edited;
schema defects are corrected by new forward migrations. Production application
rollback restores the previous approved image digest and resolves schema
incompatibility with a new forward-fix migration. Destructive Alembic downgrade
is not the production rollback strategy.

One immutable image digest supplies the web, worker, scheduler CLI, migration
job, and content seed job when applicable. Schema changes run as an explicit
migration job before application rollout, not during each web instance startup.

## Detailed rules

### Migration history and schema contract

- Historical Alembic revision files are immutable.
- Corrective work adds a new forward revision and verifies migrated data and
  constraints.
- The repository maintains one Alembic head.
- ORM metadata and the migrated schema converge.
- `alembic check` becomes a clean release gate after the known drift owned by
  Issue #15 is repaired. Until then, the exact audited drift manifest remains
  an explicit baseline failure contract rather than being ignored.
- A downgrade may exist for safe development and test workflows, but its
  presence does not make it a supported production recovery path.

### Deployment sequence

Production deployment follows this order:

1. verify backup and point-in-time-recovery readiness;
2. create or verify the pre-deploy snapshot required by the runbook;
3. run the migration job from the approved immutable image digest;
4. verify migration completion, expected head, and required data/constraint
   checks;
5. deploy that approved digest to web and worker roles;
6. run health, trust-boundary, data-readiness, and Telegram smoke tests;
7. enable scheduled delivery only through its separate release gate.

The content seed job, when required, uses the same digest and an explicit,
versioned, idempotent command.

### Rollback and recovery

If an application release fails, operators disable scheduler or delivery when
needed and restore the previous approved image digest. Any incompatible schema
condition is repaired by a new forward-fix migration.

Database restore is reserved for confirmed data corruption or data loss and
follows the backup/restore runbook. It is not an automatic response to a failed
application deploy. A development/test downgrade may be implemented and tested
when safe, but production procedures do not depend on it.

### Compatibility strategy

Potentially incompatible changes use expand/contract:

1. add a backward-compatible new schema;
2. deploy code compatible with old and new representations;
3. backfill and verify data;
4. switch readers and writers under explicit gates;
5. remove the legacy schema in a separate later migration after compatibility
   is proven.

Outbox, webhook, worker, and previous-image compatibility must be considered
for every schema transition because durable jobs can outlive a process rollout.

## Consequences

### Positive consequences

- A revision identifier has one stable meaning across every environment.
- Production rollback avoids routine destructive database operations.
- Build-once image promotion makes migration and runtime code traceable.
- Expand/contract supports safe application rollback while durable work exists.

### Negative consequences / accepted trade-offs

- Corrective migrations accumulate instead of producing a cosmetically clean
  history.
- Forward fixes may take longer than a simple downgrade and require compatible
  application design.
- Expand/contract needs extra migrations, temporary fields, and verification
  before legacy schema removal.

### Operational consequences

- Backup/PITR and pre-deploy snapshot readiness are hard deployment gates.
- Migration, data verification, image digest, smoke, rollback, and restore-drill
  evidence must be retained without exposing personal data or secrets.
- Failed migrations stop deployment before web/worker rollout; schema changes
  are never hidden in ordinary application startup.

## Rejected alternatives

- **Edit historical revisions.** Rejected because deployed environments would
  disagree about schema at the same revision. This is not reconsidered for
  production history; corrections use new revisions.
- **Use destructive downgrade as production rollback.** Rejected because data
  and constraints may not be reversibly reconstructible. Safe dev/test
  downgrades remain useful but are not promoted to production strategy.
- **Automatically restore the database after a failed application deploy.**
  Rejected because restore can discard valid writes made after the snapshot.
  Restore is reconsidered only for confirmed corruption or loss under the
  recovery runbook.
- **Use different unverified images for web, worker, and migrations.** Rejected
  because code/schema compatibility becomes untraceable. A future split would
  require independent artifact contracts and a new ADR.
- **Run schema changes at every web instance startup.** Rejected because
  concurrent startup creates lock, ordering, and partial-rollout hazards.
  Migrations remain an explicit singleton deployment job.

## Pilot boundary

The pilot keeps one Alembic head, adds only corrective forward revisions, uses
one approved image digest for every process/job role, and gates rollout on
backup readiness, migration verification, and smoke tests. Production rollback
uses the previous image plus forward fix; scheduled delivery remains separately
disabled until approved.

## Post-pilot evolution

Later schema changes continue append-only history and expand/contract where
compatibility is not immediate. A change to migration tooling, artifact
ownership, multi-region coordination, or production recovery semantics requires
a new ADR. Database restore remains disaster recovery, not routine deployment
rollback.

## Related decisions and backlog

- [ADR-0003: PostgreSQL Transactional Outbox](0003-postgresql-transactional-outbox.md)
- [Issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Tracking Issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Tracking Issue #15 — Repair Alembic and schema drift](https://github.com/smytsyk-beep/a_daily/issues/15)
- [Tracking Issue #17 — Pilot runtime and recovery foundation](https://github.com/smytsyk-beep/a_daily/issues/17)
- [Issue #47 — Snapshot upgrade and clean Alembic gates](https://github.com/smytsyk-beep/a_daily/issues/47)
- [Issue #53 — Backup policy and restore drill](https://github.com/smytsyk-beep/a_daily/issues/53)
- [Issue #54 — Pilot deploy and rollback gates](https://github.com/smytsyk-beep/a_daily/issues/54)
- [Correction plan](../Correction_plan_AstroDaily_2026-07-30.md)
- [Audited baseline and pre-production audit reference](../CODEX_HANDOFF.md#baseline)

The underlying audit artifact is referenced as `docs/preprod_code_audit.md` by
governance but is not tracked on the approved base; the Correction plan is the
tracked reconciliation of its findings.

## Verification

Affected implementation PRs must provide:

- proof that no historical revision changed and that exactly one head remains;
- fresh PostgreSQL 16 upgrade and production-like snapshot upgrade tests;
- migrated data-count, value, uniqueness, constraint, and index verification;
- a clean `alembic check` after Issue #15 closes the known drift contract;
- a safe development/test downgrade test for each new migration without
  presenting downgrade as production recovery;
- image digest equality across migration, web, worker, scheduler, and seed
  roles; migration-job failure and startup-concurrency checks;
- documented deployment and rollback rehearsals, backup/PITR readiness,
  pre-deploy snapshot evidence, smoke tests, and an isolated restore drill.

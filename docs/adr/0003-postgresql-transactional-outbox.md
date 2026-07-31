# ADR-0003: PostgreSQL Transactional Outbox

- Status: Accepted
- Date: 2026-07-31
- Decision scope: Pilot / Post-pilot boundaries

## Context

The audited Telegram webhook performs database, digest, and provider work
synchronously, does not authenticate the provider request, and has no durable
update identity. Replaying an update can repeat side effects and toggle state.
Process-local caches, background tasks, or queues cannot preserve accepted work
through process crashes. The pilot requires a durable boundary without adding
a second distributed data system.

## Decision

PostgreSQL is the pilot source of truth, durable inbound-update ledger,
transactional outbox queue, and delivery/idempotency store. The web service and
worker provide at-least-once processing. Business side effects and job creation
must be idempotent; AstroDaily does not claim exactly-once external message
delivery.

The first pilot uses one web instance, one worker, managed scheduler enqueue,
and a PostgreSQL transactional outbox. It does not use Redis, Celery, RabbitMQ,
Kafka, or another broker.

## Detailed rules

### Durable identities and state

The conceptual records and mandatory invariants are:

- `telegram_updates` has a unique provider `update_id`;
- `outbox_jobs` has a unique `dedupe_key` representing the business job;
- `telegram_deliveries` has a unique outbound delivery identity;
- retries, attempt state, availability, processing ownership or lease,
  completion, and dead-letter state are durable;
- process-local memory is never the source of truth for accepted updates,
  jobs, deliveries, or idempotency.

This ADR does not prescribe final column definitions or a migration. Those
belong to the implementing issues and must preserve these invariants.

### Processing guarantee

- Processing and external messaging are at least once.
- Business mutations and downstream job creation are safe under replay.
- Inbound update identity and outbound job identity are unique.
- State commands write the desired value: snooze writes disabled/quiet state,
  resume writes enabled/active state, and repeated commands do not toggle.
- Retryable failures use retry and backoff; exhausted or non-retryable work has
  an inspectable dead-letter state.
- Worker crashes and stale processing locks recover without losing the job.
- No component promises exactly-once provider delivery when the external
  provider cannot guarantee it.

### Webhook transaction boundary

The implemented webhook must:

1. verify the provider secret before processing;
2. minimally parse the update and extract its identity;
3. in one database transaction, store the inbound identity and its outbox job;
4. create no second job when the unique update already exists;
5. commit;
6. return HTTP 200 before geocoding, digest generation, LLM work, or provider
   send.

FastAPI `BackgroundTasks` and process-local queues are not durable substitutes
for this transaction.

### Worker boundary

The worker must:

- claim ready jobs with row locking such as `FOR UPDATE SKIP LOCKED`;
- use a bounded processing lease or equivalent stale-lock recovery;
- classify retryable and non-retryable errors;
- implement retry, backoff, dead-letter handling, completed-job cleanup, and
  graceful shutdown;
- recover claimed work after a worker crash;
- commit business mutation and subsequent outbound jobs transactionally;
- use a provider idempotency capability when one exists, while still keeping
  local delivery identity;
- keep provider payloads and identifiers at the adapter boundary.

Managed scheduler invocations enqueue durable jobs and never send messages
directly. Scheduled delivery remains disabled until its separate release gate.

## Consequences

### Positive consequences

- Acknowledged updates survive web or worker crashes.
- One database transaction closes the gap between inbound persistence and job
  creation.
- Duplicate updates, commands, and jobs have testable identities.
- The pilot avoids operating a second stateful distributed system.

### Negative consequences / accepted trade-offs

- PostgreSQL carries queue traffic and requires careful indexes, cleanup, and
  lock discipline.
- At-least-once behavior requires every business effect to be designed for
  replay.
- External sends can still be duplicated at ambiguous provider failure
  boundaries; exactly-once claims are intentionally excluded.

### Operational consequences

- Operators need queue age, retry, dead-letter, lease, and delivery metrics
  without exposing them publicly.
- Worker shutdown, crash recovery, stale locks, and duplicate delivery must be
  exercised before pilot approval.
- Retention and cleanup policies must preserve auditability without retaining
  raw provider payloads or personal data longer than approved.

## Rejected alternatives

- **FastAPI `BackgroundTasks` as the queue.** Rejected because acknowledged
  work can disappear on process termination. It remains suitable only for
  non-durable, non-business cleanup.
- **A process-local in-memory queue.** Rejected because it has no crash recovery
  or shared durable identity. It is not reconsidered for accepted business
  work.
- **Celery with Redis for the first pilot.** Rejected because it adds a broker,
  worker framework, and another failure domain without measured need. A later
  broker requires a new ADR and operational evidence.
- **Redis Streams as the source of truth.** Rejected because PostgreSQL owns the
  transaction and idempotency records. Redis may later support cache or rate
  limiting after multi-instance approval, but is not the canonical queue.
- **Exactly-once external delivery.** Rejected because local transactions
  cannot guarantee provider-side exactly-once effects. Reconsider only if a
  provider exposes a verified idempotency contract; local semantics remain
  explicit.
- **Heavy synchronous work before webhook acknowledgement.** Rejected because
  it increases provider retries, request latency, and duplicate side effects.
  Only minimal verification, parsing, and transactional enqueue stay in the
  request.

## Pilot boundary

The pilot has one public web instance, one worker, PostgreSQL outbox state, and
a managed scheduler capable only of enqueue. Redis, Celery, RabbitMQ, Kafka,
and other canonical queues are absent. Scheduled delivery is not enabled until
its dedicated gate passes.

## Post-pilot evolution

A broker or alternative queue may be considered only through a new ADR backed
by measured capacity, isolation, reliability, or operational needs. Redis may
be considered separately for shared cache or distributed rate limiting only
after more than one web instance is approved. It does not automatically replace
PostgreSQL as source of truth or canonical queue.

## Related decisions and backlog

- [ADR-0002: Channel-Agnostic Modular Monolith](0002-channel-agnostic-modular-monolith.md)
- [ADR-0004: Forward-Only Production Migrations](0004-forward-only-production-migrations.md)
- [Issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Tracking Issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Tracking Issue #20 — Secure Telegram outbox processing](https://github.com/smytsyk-beep/a_daily/issues/20)
- [Tracking Issue #24 — Scheduled local-time delivery](https://github.com/smytsyk-beep/a_daily/issues/24)
- [Tracking Issue #30 — Extended operational hardening](https://github.com/smytsyk-beep/a_daily/issues/30)
- [Correction plan](../Correction_plan_AstroDaily_2026-07-30.md)
- [Audited baseline and pre-production audit reference](../CODEX_HANDOFF.md#baseline)

The underlying audit artifact is referenced as `docs/preprod_code_audit.md` by
governance but is not tracked on the approved base; the Correction plan is the
tracked reconciliation of its findings.

## Verification

Affected implementation PRs must provide:

- database constraint and concurrent transaction tests for update, job, and
  delivery uniqueness;
- webhook tests for missing, invalid, and valid secrets, duplicate updates,
  one-transaction enqueue, and fast HTTP 200 before heavy work;
- replay tests proving desired-state commands and business mutations are
  idempotent;
- worker tests for `SKIP LOCKED` claims, lease expiry, stale-lock recovery,
  crash/restart, retry/backoff, dead-letter, cleanup, and graceful shutdown;
- provider failure-boundary tests documenting possible duplicate sends and any
  provider idempotency behavior;
- evidence that no in-memory queue, Redis, Celery, RabbitMQ, or Kafka became the
  pilot source of truth.

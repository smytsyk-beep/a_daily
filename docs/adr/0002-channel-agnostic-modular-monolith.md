# ADR-0002: Channel-Agnostic Modular Monolith

- Status: Accepted
- Date: 2026-07-31
- Decision scope: Pilot / Post-pilot boundaries

## Context

The current Telegram router mixes transport parsing, onboarding, persistence,
plan resolution, digest orchestration, rendering, and provider calls. Keeping
Telegram-specific types and identifiers in core contracts would duplicate
business behavior for every later channel. Splitting the pilot into services
would add deployment and failure complexity before independent scaling or
ownership needs have been demonstrated.

## Decision

AstroDaily remains one channel-agnostic modular monolith. It has four logical
layers: domain, application, infrastructure, and adapters. Telegram is the
first transport adapter, not a domain boundary. All channels use the same
application use cases and channel-neutral messaging contracts.

The first pilot uses one deployable application codebase, one public web
service, one background worker, a managed scheduler, managed PostgreSQL, and
one region. It does not use microservices or Kubernetes.

## Detailed rules

### Dependency direction

- The domain layer contains business concepts and rules. It does not import
  application, infrastructure, adapters, FastAPI, Telegram, provider HTTP
  clients, or ORM concerns.
- The application layer uses domain types and declares ports, use cases,
  transaction boundaries, and channel-neutral input/output contracts.
- Infrastructure implements persistence and external-provider ports without
  becoming the owner of business policy.
- Adapters translate transport-specific input and output. FastAPI routers,
  Telegram parsing/rendering/client calls, worker and scheduler entrypoints,
  and the admin CLI belong here.
- Astro core, plans, digest selection, onboarding rules, and RAG do not depend
  on Telegram or any future provider.

### Channel-neutral contracts

The shared contracts include:

- `ChannelIdentity`, containing channel, external user identity, conversation
  identity, locale, and safe channel metadata;
- `InboundMessage`, containing a channel-neutral message identity, dedupe key,
  semantic action or command, input payload, timestamp, and correlation ID;
- `OutboundMessage`, containing channel identity, semantic content or
  translation key, template data, semantic actions, correlation ID, and an
  idempotency key;
- `MessagingChannel`, the port for send, interactive acknowledgement,
  capability checks, and normalized retryable/non-retryable errors;
- `ChannelRenderer`, which creates provider-specific payloads only at the
  adapter boundary;
- application use cases that accept primitives or application DTOs rather
  than FastAPI requests, Telegram updates, or `chat_id`.

Telegram callback data is converted to a semantic action inside the Telegram
adapter. Telegram IDs, Markdown, keyboard JSON, and provider payloads do not
enter domain contracts. Future WhatsApp, Viber, PWA, or Web adapters reuse the
same use cases; they do not receive separate domain implementations.

### Deployment shape

The pilot components are process roles of one modular system and one immutable
codebase. The web service accepts the approved public HTTP surface, the worker
executes durable jobs, and the managed scheduler invokes an enqueue entrypoint.
PostgreSQL supplies durable coordination as defined in ADR-0003.

## Consequences

### Positive consequences

- Business behavior can be tested without Telegram or FastAPI.
- A later channel can be added through adapter and contract tests without
  changing plans, digest, RAG, or astro core.
- One codebase and deployment artifact keep pilot operations understandable.
- Module boundaries remain available for later extraction if evidence demands
  it.

### Negative consequences / accepted trade-offs

- The monolith requires disciplined imports and clear module ownership.
- A single repository and release cadence remain shared across modules.
- Existing mixed Telegram code must be incrementally wrapped and extracted by
  later issues rather than rewritten in this documentation issue.

### Operational consequences

- Architecture import-boundary tests are release gates.
- Web, worker, scheduler, migrations, and optional seed jobs use the same code
  and image digest but different commands.
- One-region and single-web-instance assumptions must be explicit in capacity,
  cache, and failure reviews.

## Rejected alternatives

- **Telegram-centric business architecture.** Rejected because provider types
  would become permanent core contracts. It is not reconsidered for shared
  domain behavior; provider capabilities remain adapter concerns.
- **Separate business logic for each messenger.** Rejected because it creates
  divergent plans, onboarding, digest, and idempotency rules. A provider may
  add only capability-specific adapter behavior.
- **Microservices before measured necessity.** Rejected because the pilot has
  no demonstrated independent scaling, ownership, release, or failure-isolation
  boundary. Extraction requires a new ADR backed by one or more such needs or
  by measured load the modular monolith cannot serve.
- **Kubernetes for the first pilot.** Rejected because one web process and one
  worker do not justify its operational cost. Reconsideration requires an
  approved runtime/scaling decision and a new ADR.
- **Keep one large Telegram router permanently.** Rejected because it violates
  adapter and use-case boundaries. It may remain temporarily while focused
  backlog issues extract behavior with regression tests.

## Pilot boundary

The pilot deploys one application codebase as one public web service and one
worker, with a managed scheduler and PostgreSQL in one region. Telegram is the
only live messaging adapter. There are no microservices, Kubernetes resources,
provider-specific domain contracts, or channel-specific business variants.

## Post-pilot evolution

A second messaging adapter requires its provider/capability decision and must
pass the existing shared contract tests without changing core behavior.
Internal and public HTTP adapters follow ADR-0001. Extracting a module into a
service requires a new ADR and evidence such as independent scaling, ownership,
release cadence, required failure isolation, or measured load that the modular
monolith can no longer serve. No invented numeric threshold is part of this
decision.

## Related decisions and backlog

- [ADR-0001: Production HTTP Trust Boundary](0001-production-http-trust-boundary.md)
- [ADR-0003: PostgreSQL Transactional Outbox](0003-postgresql-transactional-outbox.md)
- [Issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Tracking Issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Tracking Issue #18 — Channel-neutral user identities](https://github.com/smytsyk-beep/a_daily/issues/18)
- [Tracking Issue #19 — Channel-neutral application use cases](https://github.com/smytsyk-beep/a_daily/issues/19)
- [Tracking Issue #20 — Secure Telegram outbox processing](https://github.com/smytsyk-beep/a_daily/issues/20)
- [Tracking Issue #27 — Second messaging-channel adapter](https://github.com/smytsyk-beep/a_daily/issues/27)
- [Tracking Issue #31 — P2 cleanup and documentation](https://github.com/smytsyk-beep/a_daily/issues/31)
- [Correction plan](../Correction_plan_AstroDaily_2026-07-30.md)
- [Audited baseline and pre-production audit reference](../CODEX_HANDOFF.md#baseline)

The underlying audit artifact is referenced as `docs/preprod_code_audit.md` by
governance but is not tracked on the approved base; the Correction plan is the
tracked reconciliation of its findings.

## Verification

Affected implementation PRs must provide:

- automated import-boundary tests for domain, application, infrastructure, and
  adapters;
- unit tests for use cases using fake repositories and a fake messaging
  channel without FastAPI or Telegram imports;
- contract tests for inbound/outbound DTOs, semantic actions, renderer output,
  provider error mapping, and capability handling;
- a proof test that another fake channel can use plans, digest, onboarding, RAG,
  and astro core without modifications;
- deployment evidence that pilot process roles share one approved codebase and
  image digest and that no microservice or Kubernetes dependency was added.

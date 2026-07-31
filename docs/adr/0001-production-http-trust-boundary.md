# ADR-0001: Production HTTP Trust Boundary

- Status: Accepted
- Date: 2026-07-31
- Decision scope: Pilot / Post-pilot boundaries

## Context

The audited FastAPI application registers user data, mutations, diagnostics,
events, preview, calendar, module, and documentation routes without a complete
authentication and object-authorization boundary. The first production pilot
needs only a health probe and Telegram ingress. Treating the existing route
inventory as a public API would expose personal and operational data and would
prematurely couple future internal and end-user clients to one trust model.

## Decision

The public HTTP surface for the first production pilot is exactly:

- `GET /health`;
- `POST /telegram/webhook`.

No other application route is registered on the public production app. An
internal service API and a public PWA/Web API are separate post-pilot products
with different identities, authorization, and network boundaries. AstroDaily
does not provide a public administration API.

## Detailed rules

### Public pilot routes

`GET /health` returns only a coarse safe status. It does not expose database
counts, configuration, secrets, internal exception details, or diagnostic
inventory.

`POST /telegram/webhook` is the only public business ingress. Its implementation
must verify the Telegram webhook secret before processing, preserve unique
update identity, and enqueue work idempotently. Those controls are implemented
by later backlog issues, not by this ADR.

### Routes absent from public production

The pilot production app does not register:

- `/docs`, `/redoc`, or `/openapi.json`;
- `/metrics` or `/db/health`;
- preference, birth-data, summary, module, alert, calendar, event, feedback,
  preview, or admin endpoints;
- a public `/api/v1`.

Calendar is disabled for the first pilot. Database readiness and metrics, when
needed by the platform, remain private and authenticated rather than becoming
public application routes.

### Separate post-pilot trust models

An internal service API is considered only after a concrete internal consumer
exists. It uses `/internal/v1`, service identity and authentication, narrowly
scoped authorization, private-network policy, and audit logs.

A public PWA/Web API uses `/api/v1`, end-user authentication, object-level
authorization, and its own CORS, CSRF, rate-limit, session or token lifecycle,
and public error rules. It does not reuse an unrestricted internal service
credential. The internal and public APIs require separate threat reviews and
cannot be combined under one token model.

### Administration

Manual entitlement operations use a private, audit-logged admin CLI. Raw SQL is
not a supported operator procedure, and a public admin API is not created.

## Consequences

### Positive consequences

- The pilot has a small, testable public attack surface.
- Existing unauthenticated routes cannot accidentally become production
  contracts.
- Internal automation and end-user applications can evolve with correct,
  independent authorization models.

### Negative consequences / accepted trade-offs

- Existing development routes are unavailable in public production.
- Calendar, PWA, and HTTP-based operational conveniences are deferred.
- Operators need private platform probes and CLI workflows instead of public
  diagnostic or administrative endpoints.

### Operational consequences

- Production startup and black-box tests must fail closed when an unapproved
  route, docs surface, or unsafe setting is present.
- Health responses and public errors require explicit disclosure tests.
- Private ingress, credentials, audit retention, and route flags must be
  managed independently from public ingress.

## Rejected alternatives

- **Publish all current FastAPI routes.** Rejected because the audited routes
  lack a unified authentication and object-authorization boundary. Individual
  routes may return only through a separately approved internal or public API
  decision and its tests.
- **Protect routes only with secret or unlisted URLs.** Rejected because URL
  secrecy is not authentication or authorization. This is not reconsidered as
  a security control.
- **Use one bearer token model for internal services and PWA users.** Rejected
  because service identity and end-user ownership have different threats and
  privileges. Any future convergence would require a new ADR and threat model.
- **Add a public admin API for the pilot.** Rejected because it expands the
  highest-risk mutation surface without a pilot need. Reconsideration requires
  a concrete consumer, authorization design, audit controls, and a new ADR.
- **Publish calendar by raw `user_id`.** Rejected because identifiers are not
  authorization. Post-pilot calendar access requires its separately approved
  opaque-token lifecycle and entitlement checks.

## Pilot boundary

The public ingress contains only the safe health route and Telegram webhook.
Docs, diagnostics, user APIs, calendar, metrics, preview, events, feedback,
administration, and `/api/v1` are absent. No internal API is mounted merely to
preserve existing routes.

## Post-pilot evolution

`/internal/v1` may be introduced for a specific private service consumer under
its own service-authentication decision. `/api/v1` may be introduced for PWA or
Web users under a separate end-user authentication and authorization decision.
Calendar requires its own signed subscription design. None of these additions
may silently broaden the pilot router.

## Related decisions and backlog

- [ADR-0002: Channel-Agnostic Modular Monolith](0002-channel-agnostic-modular-monolith.md)
- [Issue #34](https://github.com/smytsyk-beep/a_daily/issues/34)
- [Tracking Issue #12](https://github.com/smytsyk-beep/a_daily/issues/12)
- [Tracking Issue #13 — Pilot production API boundary](https://github.com/smytsyk-beep/a_daily/issues/13)
- [Tracking Issue #28 — Internal service API](https://github.com/smytsyk-beep/a_daily/issues/28)
- [Tracking Issue #29 — Public PWA API](https://github.com/smytsyk-beep/a_daily/issues/29)
- [Correction plan](../Correction_plan_AstroDaily_2026-07-30.md)
- [Audited baseline and pre-production audit reference](../CODEX_HANDOFF.md#baseline)

The underlying audit artifact is referenced as `docs/preprod_code_audit.md` by
governance but is not tracked on the approved base; the Correction plan is the
tracked reconciliation of its findings.

## Verification

Affected implementation PRs must provide:

- a production black-box route matrix proving that only the two approved
  routes are public and all listed surfaces return `404`;
- safe health-response and public-error schema tests;
- missing, invalid, and valid Telegram webhook-secret tests plus duplicate
  update tests;
- trusted-host, environment, private-ingress, authentication, authorization,
  and audit tests appropriate to any later internal or public API;
- confirmation that no public admin endpoint or raw-SQL operator procedure was
  introduced.

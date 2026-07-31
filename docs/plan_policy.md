# Canonical plan and digest policy

`common.plans` is AstroDaily's single channel-neutral source of truth for plan
codes, legacy normalization, runtime configuration, effective entitlement
resolution, feature checks, and digest policy. It has no Telegram, FastAPI, or
provider dependency and performs no database work at import time.

## Canonical types and APIs

- `PlanCode`: `demo`, `daily`, `full`, and `internal`.
- `DigestLength`: `short`, `medium`, and `long`.
- `PlanFeature`: `daily_digest`, `quiet_mode`, `strong_alerts`, and
  `calendar_ics`.
- `PlanRuntimeConfig`: immutable maximum plan capabilities.
- `DigestPolicy`: immutable requested and resolved digest decision.

The explicit public APIs are:

```python
normalize_plan_code(raw) -> PlanCode
get_plan_config(plan_code) -> PlanRuntimeConfig
get_user_plan_code(db, user_id, *, now=None) -> PlanCode
get_user_plan_config(db, user_id, *, now=None) -> PlanRuntimeConfig
plan_allows_feature(plan_code, feature) -> bool
resolve_digest_policy(plan_code, requested_length) -> DigestPolicy
```

`PlanCode` identifies a plan. `PlanRuntimeConfig` describes its maximum
capabilities. `DigestPolicy` records a particular requested length, clamped
final length, and atom cap. These values are intentionally different types.

## Normalization and default

The absence of an effective entitlement and every unknown plan value resolve
to `demo`. Input is stripped and compared case-insensitively. Legacy database
values normalize as follows:

| Legacy value | Canonical plan |
|---|---|
| `basic` | `daily` |
| `pro` | `full` |
| `free` | `daily` |
| `premium` | `full` |

## Plan configuration

| Plan | Maximum length | Atom cap | Features |
|---|---|---:|---|
| `demo` | `short` | 2 | daily digest |
| `daily` | `medium` | 3 | daily digest, quiet mode |
| `full` | `long` | 6 | daily digest, quiet mode, strong alerts, calendar |
| `internal` | `long` | 6 | daily digest, quiet mode, strong alerts, calendar |

Calendar remains disabled at the production pilot HTTP boundary. The matrix
does not expose calendar or strong alerts to `demo` or `daily`.

## Digest resolution

Shorter user preferences are preserved. The atom cap is derived from the
final length, never independently from the plan.

| Plan | Requested short | Requested medium | Requested long |
|---|---|---|---|
| `demo` | short / 2 | short / 2 | short / 2 |
| `daily` | short / 2 | medium / 3 | medium / 3 |
| `full` | short / 2 | medium / 3 | long / 6 |
| `internal` | short / 2 | medium / 3 | long / 6 |

A missing or unsupported requested length resolves explicitly to `short / 2`.
The pure resolver has no database, framework, transport, or mutable global
state.

## Effective entitlement and UTC boundary

An entitlement is effective when all of these are true:

- `user_id` matches;
- `active = true`;
- `started_at <= now`;
- `expires_at IS NULL` or `expires_at > now`.

An entitlement starting exactly at `now` is effective. One expiring exactly
at `now` is not. Future, expired, inactive, missing, and unknown-plan rows
resolve to `demo`.

The current columns are PostgreSQL `timestamp without time zone`. Existing
values are treated as naive UTC only inside the canonical repository reader.
The reader obtains an aware UTC clock with `datetime.now(timezone.utc)`,
converts an explicitly supplied aware instant to naive UTC for the current
schema, and rejects supplied naive datetimes. This compatibility boundary is
removed only with a separately approved schema change.

Until Issue #43 enforces one active entitlement, multiple effective rows are
resolved deterministically by latest `started_at`, then highest `id`. If that
winning row has an unknown plan, the result is `demo`; the reader does not fall
back to an older row that could grant more access.

## Compatibility and issue boundaries

Legacy names in `common.plans`, `common.entitlements`, and `app.plan_service`
are deprecated delegators. They contain no second matrix or entitlement SQL
and remain temporarily so Issue #38 does not perform a broad caller rewrite.

- Issue #42 migrates route, service, worker, feature-flag, and direct digest
  callers to these explicit APIs and removes presence-based entitlement
  bypasses and local cap calculations.
- Issue #43 normalizes stored entitlement data and adds window/plan and
  one-active database constraints.
- Issue #46 adds the private audit-logged administration CLI.

Example channel-neutral usage:

```python
plan_code = get_user_plan_code(db, user_id, now=instant)
policy = resolve_digest_policy(plan_code, requested_length)
```

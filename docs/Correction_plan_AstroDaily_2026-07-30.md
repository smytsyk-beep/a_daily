# План исправления AstroDaily

**Документ:** `docs/Correction_plan_AstroDaily_2026-07-30.md`
**Основание:** `docs/preprod_code_audit.md`
**Текущий статус:** Production **NO-GO**

## Implementation status

- Remediation status: Issues #35 and #36 completed via PRs #61 and #62; the
  next implementation issue is not selected.
- Application code changes: none active; the production router boundary is
  merged in `main`.
- Active release wave: **Wave A — Mandatory Foundation**.
- Active GitHub milestone:
  [Wave A — Mandatory Foundation (Pilot Gate)](https://github.com/smytsyk-beep/a_daily/milestone/1).
- Current tracking issue:
  [#13 — Enforce the pilot production API boundary](https://github.com/smytsyk-beep/a_daily/issues/13).
- Current implementation issue: not selected.
- ADR status: accepted and merged; the canonical index is
  [docs/adr/README.md](adr/README.md).
- Completed GitHub issues:
  [#32 — Establish repository governance and Codex handoff](https://github.com/smytsyk-beep/a_daily/issues/32)
  and
  [#33 — Make the audited test and migration baseline reproducible](https://github.com/smytsyk-beep/a_daily/issues/33),
  and
  [#34 — Record trust-boundary, modular-monolith, outbox, and migration ADRs](https://github.com/smytsyk-beep/a_daily/issues/34),
  and
  [#35 — Add fail-fast production settings and secret validation](https://github.com/smytsyk-beep/a_daily/issues/35),
  and
  [#36 — Register only health and Telegram webhook on the public production app](https://github.com/smytsyk-beep/a_daily/issues/36).
- GitHub backlog created: 3 milestones, 17 project labels, 20 tracking issues,
  and 23 Wave A implementation issues.
- Wave B and Wave C implementation issues remain decomposed in this document
  and have not been created.
- Repository governance is defined in `AGENTS.md`.
- Cross-chat baseline and active-work context are maintained in
  `docs/CODEX_HANDOFF.md`.

Release waves:

- **Wave A — Mandatory Foundation:** stages 0, 3, 6, 7, 8 and the pilot-blocking
  subset of stage 13.
- **Wave B — Telegram Production Path:** stages 1, 2, 4, 5, 9 and 12.
- **Wave C — Post-Pilot:** stages 10, 11, extended content cooldown, a second
  channel adapter, a separately authenticated internal service API, an
  independently authenticated public PWA `/api/v1`, extended stage 13
  hardening, and stage 14 cleanup.

Update this section only when a GitHub issue is selected, completed, blocked,
or when a release decision changes. Detailed implementation state remains in
GitHub issues and pull requests; issue descriptions and historical conversation
notes do not belong here.

## GitHub remediation backlog

### Created GitHub object boundary

The approved first GitHub creation batch was completed on 2026-07-30:

1. All three release-wave milestones.
2. All tracking issues for Waves A, B, and C.
3. Wave A implementation issues only.

Wave B and Wave C implementation issues remain documented below and must not be
created in GitHub during the first batch.

### Required labels

- `priority:P0`, `priority:P1`, `priority:P2`
- `release:pilot`, `release:post-pilot`
- `area:security`, `area:database`, `area:telegram`
- `area:architecture`, `area:infra`, `area:content`, `area:testing`
- `type:bug`, `type:feature`, `type:refactor`, `type:docs`
- `blocked`

`blocked` is applied only for an actual unresolved product, access, or external
dependency. An ordinary dependency on another backlog issue does not by itself
receive the label.

### Milestones

| Milestone | Release boundary |
|---|---|
| `Wave A — Mandatory Foundation (Pilot Gate)` | Security, schema, plans, profile correctness, production artifact, and recovery foundation required before real users. |
| `Wave B — Telegram Production Path (Pilot Gate)` | Channel-neutral Telegram path required for a stable manual `/today`; scheduled delivery and calendar remain disabled. |
| `Wave C — Post-Pilot Functionality` | Scheduled delivery, calendar, advanced content behavior, new clients/channels, and P2 cleanup. |

Milestones have no due date until a delivery date is explicitly approved.

### Tracking issues

| ID | Tracking issue | Milestone | Labels | Dependencies |
|---|---|---|---|---|
| TA0 | `[TRACKING][A0] Baseline, governance and architecture decisions` | Wave A | `priority:P0`, `release:pilot`, `area:architecture`, `area:testing`, `type:docs` | None |
| TA3 | `[TRACKING][A3] Enforce the pilot production API boundary` | Wave A | `priority:P0`, `release:pilot`, `area:security`, `type:bug` | TA0 |
| TA6 | `[TRACKING][A6] Make plans and entitlements canonical and safe` | Wave A | `priority:P0`, `release:pilot`, `area:database`, `area:architecture`, `type:bug` | TA0 |
| TA7 | `[TRACKING][A7] Repair Alembic and schema drift` | Wave A | `priority:P0`, `release:pilot`, `area:database`, `type:bug` | TA0 |
| TA8 | `[TRACKING][A8] Prevent timezone and profile-data corruption` | Wave A | `priority:P0`, `release:pilot`, `area:database`, `area:architecture`, `type:bug` | TA0 |
| TA13 | `[TRACKING][A13] Build the pilot runtime and recovery foundation` | Wave A | `priority:P0`, `release:pilot`, `area:infra`, `type:feature` | TA3, TA7 |
| TB1 | `[TRACKING][B1] Introduce channel-neutral user identities` | Wave B | `priority:P0`, `release:pilot`, `area:database`, `area:architecture`, `type:feature` | TA7 |
| TB2 | `[TRACKING][B2] Extract minimum channel-neutral application use cases` | Wave B | `priority:P0`, `release:pilot`, `area:architecture`, `type:refactor` | TA0, TA6 |
| TB4 | `[TRACKING][B4] Implement secure Telegram outbox processing` | Wave B | `priority:P0`, `release:pilot`, `area:telegram`, `area:database`, `type:feature` | TA3, TB1, TB2 |
| TB5 | `[TRACKING][B5] Move onboarding into an explicit state machine` | Wave B | `priority:P0`, `release:pilot`, `area:telegram`, `area:architecture`, `type:refactor` | TA8, TB1, TB2, TB4 |
| TB9 | `[TRACKING][B9] Canonicalize digest events, cache and production content` | Wave B | `priority:P0`, `release:pilot`, `area:content`, `area:database`, `type:bug` | TA6, TA7, TA8, TB2 |
| TB12 | `[TRACKING][B12] Add pilot-safe logging, privacy and observability` | Wave B | `priority:P0`, `release:pilot`, `area:security`, `area:infra`, `type:refactor` | TA3, TB4 |
| TC10 | `[TRACKING][C10] Enable scheduled local-time delivery` | Wave C | `priority:P1`, `release:post-pilot`, `area:telegram`, `area:infra`, `type:feature` | TA13, TB4, TB5, TB9, TB12 |
| TC11 | `[TRACKING][C11] Add signed calendar subscriptions and migrate legacy calendar events` | Wave C | `priority:P1`, `release:post-pilot`, `area:security`, `area:content`, `type:feature` | TA6, TB9, TB12 |
| TC9X | `[TRACKING][C9+] Add persistent digest history and extended content cooldown` | Wave C | `priority:P1`, `release:post-pilot`, `area:content`, `area:database`, `type:feature` | TB9 |
| TC2X | `[TRACKING][C2+] Add a second messaging-channel adapter` | Wave C | `priority:P2`, `release:post-pilot`, `area:architecture`, `type:feature` | TB1, TB2, TB4 |
| TC3I | `[TRACKING][C3I] Add an authenticated internal service API` | Wave C | `priority:P1`, `release:post-pilot`, `area:security`, `area:architecture`, `type:feature` | TA3, TB2, TB12 |
| TC3P | `[TRACKING][C3P] Add an authenticated public PWA API v1` | Wave C | `priority:P2`, `release:post-pilot`, `area:security`, `area:architecture`, `type:feature` | TA3, TB2, TB12 |
| TC13X | `[TRACKING][C13+] Extend CI/CD and operational hardening` | Wave C | `priority:P2`, `release:post-pilot`, `area:infra`, `type:feature` | TA13, TB12 |
| TC14 | `[TRACKING][C14] Complete P2 cleanup and documentation` | Wave C | `priority:P2`, `release:post-pilot`, `area:architecture`, `type:refactor` | Wave B complete |

Tracking issue creation total: **20**.

### Wave A implementation issues to create

Every issue below also receives `release:pilot`.

| ID | Implementation issue | Labels | Dependencies | Risk |
|---|---|---|---|---|
| A0.1 | Establish repository governance and Codex handoff | `priority:P0`, `area:architecture`, `type:docs` | None | Low |
| A0.2 | Make the audited test and migration baseline reproducible | `priority:P0`, `area:testing`, `type:feature` | A0.1 | Medium |
| A0.3 | Record trust-boundary, modular-monolith, outbox, and migration ADRs | `priority:P0`, `area:architecture`, `type:docs` | A0.1 | Low |
| A3.1 | Add fail-fast production settings and secret validation | `priority:P0`, `area:security`, `type:bug` | A0.3 | High |
| A3.2 | Register only `/health` and Telegram webhook on the public production app | `priority:P0`, `area:security`, `type:bug` | A3.1 | High |
| A3.4 | Add trusted-host, safe-error, and production route-exposure tests | `priority:P0`, `area:security`, `area:testing`, `type:bug` | A3.2 | High |
| A6.1 | Consolidate the canonical plan and digest-policy service | `priority:P0`, `area:architecture`, `type:refactor` | A0.3 | High |
| A6.2 | Route every pilot feature gate and digest cap through canonical policy | `priority:P0`, `area:security`, `type:bug` | A6.1 | High |
| A6.3 | Normalize entitlement data and enforce one active entitlement | `priority:P0`, `area:database`, `type:bug` | **A7.1**, A6.1 | High |
| A6.4 | Add audit-logged entitlement administration CLI | `priority:P0`, `area:database`, `type:feature` | A6.3 | High |
| A7.1 | Reconcile `module_registry` into canonical `modules_registry` and establish the corrective migration base | `priority:P0`, `area:database`, `type:bug` | **A0.2, A0.3** | High |
| A7.2 | Align LLM usage types and index metadata | `priority:P0`, `area:database`, `type:bug` | A7.1 | High |
| A7.3 | Repair seed downgrade and document forward-only production recovery | `priority:P0`, `area:database`, `type:bug` | A7.1 | High |
| A7.4 | Add snapshot-upgrade and clean `alembic check` CI gates | `priority:P0`, `area:database`, `area:testing`, `type:feature` | **A6.3**, A7.2, A7.3 | High |
| A8.1 | Replace naive UTC handling with aware UTC conversions | `priority:P0`, `area:architecture`, `type:bug` | A0.3 | High |
| A8.2 | Preserve geo fields during partial birth-data updates and invalidate derived state | `priority:P0`, `area:database`, `type:bug` | A8.1 | High |
| A8.3 | Implement domain/service handling for ambiguous or nonexistent DST birth times; defer Telegram UI to B5 | `priority:P0`, `area:database`, `type:feature` | A8.1 | High |
| A8.4 | Remove unsafe geocoding fallbacks and return domain/service confirmation candidates; defer Telegram UI to B5 | `priority:P0`, `area:architecture`, `type:bug` | A8.1 | High |
| A13.1 | Build a non-root self-contained production image | `priority:P0`, `area:infra`, `type:feature` | A0.2 | High |
| A13.2 | Define managed runtime, secret, HTTPS, and private database configuration | `priority:P0`, `area:infra`, `area:security`, `type:feature` | A3.1, A13.1 | High |
| A13.3 | Implement backup policy and a repeatable restore drill | `priority:P0`, `area:infra`, `area:database`, `type:feature` | **A13.2** | High |
| A13.4 | Add pilot deploy/rollback runbook and minimum image/recovery CI gates | `priority:P0`, `area:infra`, `area:testing`, `type:docs` | A7.4, A13.1, A13.2, A13.3, **A13.5** | High |
| A13.5 | Pin dependencies and verify the ephemeris checksum in build and startup checks | `priority:P0`, `area:infra`, `area:testing`, `type:feature` | A13.1 | High |

The mandatory migration dependency is:

```text
A7.1 -> A6.3 -> A7.4
```

Wave A creation total: **23 implementation issues**.

#### Mandatory A6.4 acceptance criteria

The audit-logged entitlement CLI issue must include all of the following:

- `--dry-run` shows the proposed before/after state and performs no mutation;
- mutating commands require non-empty `actor`, `reason`, and idempotency
  operation ID;
- plan codes and activation/expiration windows are validated before locking;
- the target user row is selected with a row lock before entitlement changes;
- deactivation, insertion, effective-plan verification, and immutable audit
  before/after recording happen in one transaction;
- concurrent assignment attempts are covered by an integration test and leave
  exactly one active entitlement;
- retrying the same operation ID is idempotent and does not create another
  entitlement or audit action;
- CLI output and logs contain no database credentials, tokens, connection
  strings, or other secrets.

### Wave B implementation decomposition — do not create yet

All B5 implementation issues are `priority:P0` and `release:pilot`.

- **B1:** user-channel schema/backfill; channel identity repository and dual
  reads; removal of Telegram IDs from core callers.
- **B2:** channel-neutral messaging DTOs/ports; digest and plan use cases;
  preference/birth/feedback use cases; import-boundary and fake-channel tests.
- **B4:** Telegram update/outbox/delivery schema; inbound parser; authenticated
  fast webhook enqueue; outbound renderer/callback acknowledgement;
  desired-state command replay tests.
- **B4.4:** `SKIP LOCKED` worker processing with a bounded processing lease,
  stale-lock recovery, graceful shutdown, worker-crash recovery, retry/backoff,
  dead-letter status, completed-job cleanup, and provider-send idempotency
  behavior and tests.
- **B5.1:** channel-neutral onboarding states and separate consents —
  `priority:P0`, `release:pilot`.
- **B5.2:** birth-place confirmation and DST resolution actions —
  `priority:P0`, `release:pilot`.
- **B5.3:** preferences, delivery, continue, decline, and re-consent flows —
  `priority:P0`, `release:pilot`.
- **B5.4:** Telegram renderer and EN/ES/RU transition tests —
  `priority:P0`, `release:pilot`.
- **B9.1:** canonical event identity and repository uniqueness —
  `priority:P0`, `release:pilot`.
- **B9.2:** unified live event calculation and batch precompute —
  `priority:P0`, `release:pilot`.
- **B9.3a:** correctness-safe cache for pilot; disable unsafe reuse or use a
  complete in-process key covering plan, length, locale, interests, timezone,
  birth signature, local date, content version, and renderer version —
  `priority:P0`, `release:pilot`.
- **B9.3b:** persistent fingerprinted `digest_runs` —
  `priority:P1`, `release:post-pilot`; parent TC9X.
- **B9.4:** versioned idempotent content seed and inventory gate —
  `priority:P0`, `release:pilot`.
- **B9.5a:** replace the user-facing moon-phase stub with a real calculation —
  `priority:P0`, `release:pilot`.
- **B9.5b:** remove test atoms from all production selection paths —
  `priority:P0`, `release:pilot`.
- **B9.5c:** enforce deterministic RAG ordering and deterministic tie-breaking —
  `priority:P1`, `release:pilot`.
- **B9.5d:** migrate legacy calendar events to canonical events —
  `priority:P1`, `release:post-pilot`; parent TC11.
- **B12.1:** structured stdout logs and correlation identifiers —
  `priority:P1`, `release:pilot`.
- **B12.2:** remove debug files and redact secrets and personal data —
  `priority:P0`, `release:pilot`.
- **B12.3:** private metrics, alerts, and retention cleanup —
  `priority:P1`, `release:pilot`.
- **B12.4:** channel-neutral export and deletion flow —
  `priority:P1`, `release:pilot`.

### Wave C implementation decomposition — do not create yet

- **A3.3:** authenticated internal HTTP API, only when a concrete internal
  consumer exists — `priority:P1`, `release:post-pilot`; parent TC3I. Pilot
  production simply does not register unused routes.
- **C10:** scheduler enqueue by local time; delivery policy and unique identity;
  cohort rollout, failure, and load tests.
- **C11:** legacy calendar-event migration; hashed subscription lifecycle;
  canonical signed `.ics`; security and plan-gate tests.
- **TC9X:** persistent fingerprinted `digest_runs`; seven-day atom-history
  cooldown with deterministic fallback.
- **TC2X:** provider decision ADR; second inbound/outbound adapter; shared
  channel contract tests. Adapter implementation remains `blocked` until the
  provider decision is approved.
- **TC3I:** private internal service API; service identity/authentication,
  service scopes, private-network enforcement, audit logs, and internal API
  contract tests. It does not share a user-session authentication model with
  the PWA.
- **TC3P:** public versioned PWA `/api/v1`; end-user authentication, session or
  token lifecycle, object-level authorization, CORS, rate limits, and public
  API security tests. It does not reuse an unrestricted internal service
  credential.
- **TC13X:** immutable artifact promotion, SBOM, extended supply-chain gates,
  SLO dashboards, capacity tests, and a multi-instance readiness decision.
- **TC14:** Telegram router split; deprecated geo/plan/digest cleanup; narrow
  exception handling; separation of feedback and operational audit; final
  runbooks and channel-adapter guide.

### Implementation issue body

Every implementation issue must contain:

```markdown
## Context
Concrete audit finding and Correction plan reference.

## Scope
Only the behavior delivered by this issue.

## Out of scope
Sibling issues, deferred release work, and unrelated refactors.

## Acceptance criteria
- [ ] Verifiable behavior and contract criteria.
- [ ] No regression of the approved baseline.
- [ ] Documentation updated when a contract changes.

## Required tests
Exact unit, integration, migration, security, or container scenarios.

## Dependencies
Links to real issue numbers or `None`.

## Risk level
Low / Medium / High with a short reason.

## Parent tracking issue
- #<tracking-issue-number>
```

### Unified Definition of Done

The canonical Definition of Done is maintained in `AGENTS.md` and applies to
every implementation issue and pull request. In summary:

- all acceptance criteria and required tests pass with PR evidence;
- all relevant CI and verification commands pass;
- no unrelated changes, secrets, PII, debug artifacts, or architecture-boundary
  violations are introduced;
- migrations are new forward revisions with data/constraint verification;
- security, operational, and localization impacts are handled where relevant;
- one implementation issue maps to one focused PR;
- the PR links its implementation and parent tracking issues and documents
  scope, risk, tests, and rollback/migration behavior;
- review findings are resolved and the parent checklist plus
  `docs/CODEX_HANDOFF.md` are updated after merge.

## 1. Зафиксированные архитектурные решения

Архитектурные развилки из Аннотации 1 закрыты следующими решениями.

### HTTP API trust boundary

В первом production pilot публичными остаются только:

- `POST /telegram/webhook`;
- `GET /health`.

Calendar `.ics` в первый pilot не входит и не регистрируется в production router.

Остальные endpoints:

- отключаются в production, если не нужны runtime;
- либо выносятся под `/internal/v1`;
- защищаются service authentication;
- доступны только через private-network policy.

`/docs`, `/redoc` и `/openapi.json` в production отключаются. Публичного admin API и пользовательского `/api/v1` в pilot нет.

### Production environment

Используется:

- managed container platform;
- managed PostgreSQL;
- один public web service;
- один background worker;
- managed scheduler/cron;
- один регион для web, worker и database;
- managed HTTPS;
- private database networking.

Kubernetes и публичный PostgreSQL не используются.

### Queue и гарантии обработки

Используется PostgreSQL transactional outbox:

- `telegram_updates` с `PRIMARY KEY(update_id)`;
- `outbox_jobs` с `UNIQUE(dedupe_key)`;
- `telegram_deliveries` с `UNIQUE(user_id, local_date, delivery_kind)`.

Гарантия: **at-least-once delivery с идемпотентными business side effects**.

Команды состояния не выполняют toggle:

- `/snooze` устанавливает quiet/snoozed state;
- `/resume` снимает его;
- replay любой команды повторно записывает то же желаемое значение.

Redis не используется. Его можно добавить только при появлении нескольких web instances — для shared cache и distributed rate limiting, но не как обязательную очередь.

### Multi-channel architecture

AstroDaily остаётся channel-agnostic modular monolith:

```text
Telegram webhook
       │
       ▼
Telegram adapter ──► InboundMessage
                          │
                          ▼
                  PostgreSQL outbox
                          │
                          ▼
                   Application use case
                    │       │       │
                    ▼       ▼       ▼
                  Plans   Digest   Onboarding
                          │
                          ▼
                    OutboundMessage
                          │
                          ▼
                  ChannelRenderer
                          │
                          ▼
                  MessagingChannel
                          │
                          ▼
                     Telegram API

Future /api/v1, WhatsApp и Viber используют те же application use cases.
```

Domain/application слои не импортируют Telegram, FastAPI, WhatsApp или Viber. Микросервисы не вводятся.

---

## 2. Целевая структура modular monolith

Разделить код логически на четыре слоя:

1. `domain`:

   - пользовательский профиль;
   - onboarding state;
   - планы и feature policy;
   - delivery policy;
   - digest/event/content entities;
   - чистые бизнес-правила.

2. `application`:

   - use cases;
   - входные/выходные DTO;
   - transaction boundaries;
   - repository и channel ports.

3. `infrastructure`:

   - SQLAlchemy repositories;
   - PostgreSQL outbox;
   - migrations;
   - geocoding, ephemeris и LLM implementations.

4. `adapters`:

   - Telegram webhook parser;
   - Telegram renderer/client;
   - internal FastAPI endpoints;
   - admin CLI;
   - scheduler и worker entrypoints.

Добавить автоматические import-boundary проверки:

- `domain` не импортирует `application`, adapters, FastAPI, HTTP clients или ORM;
- `application` импортирует только domain и объявленные ports;
- adapters и infrastructure реализуют ports;
- astro core, plans и RAG не знают о каналах доставки.

---

## 3. Общие channel-neutral интерфейсы

### ChannelIdentity

Содержит:

- `channel`;
- `external_user_id`;
- `conversation_id`;
- `locale`;
- безопасную channel metadata.

### InboundMessage

Содержит:

- channel-neutral message ID;
- dedupe key;
- `ChannelIdentity`;
- тип сообщения;
- text/command;
- semantic action ID;
- location;
- timestamp;
- correlation ID.

Telegram `callback_data` преобразуется в semantic action внутри Telegram adapter и не передаётся в domain как Telegram-структура.

### OutboundMessage

Содержит:

- `user_channel_id`;
- message kind;
- locale;
- semantic content или translation key;
- template parameters;
- semantic actions;
- correlation ID;
- idempotency key.

В нём не должно быть Telegram `chat_id`, Markdown или Telegram keyboard JSON.

### MessagingChannel

Port должен поддерживать:

- отправку сообщения;
- acknowledgement интерактивного события;
- проверку channel capabilities;
- преобразование provider errors в общие retryable/non-retryable ошибки.

### ChannelRenderer

Преобразует `OutboundMessage` в channel-specific payload:

- Telegram Markdown и inline keyboard;
- в будущем WhatsApp templates;
- в будущем Viber keyboard;
- web/PWA JSON representation.

---

## 4. Этап 0 — Зафиксировать baseline

1. Создать отдельную remediation-ветку от аудированного коммита.
2. Зафиксировать baseline:

   - `100 passed`;
   - чистый `alembic upgrade head` успешен;
   - `alembic check` сейчас завершается ошибкой;
   - production verdict — NO-GO.

3. Запретить новые продуктовые функции до закрытия P0.
4. Оставить scheduled delivery выключенным.
5. Добавить architecture decision records для:

   - modular monolith;
   - HTTP trust boundary;
   - PostgreSQL outbox;
   - channel-neutral messaging;
   - forward-only production migrations.

Критерий завершения: baseline воспроизводится в CI, архитектурные решения документированы.

---

## 5. Этап 1 — Ввести channel identity и мигрировать Telegram IDs

### Новая таблица `user_channels`

Добавить:

- `id`;
- `user_id`;
- `channel`;
- `external_user_id`;
- `conversation_id`;
- `locale`;
- `metadata JSONB`;
- `active`;
- `created_at`;
- `updated_at`;
- `UNIQUE(channel, external_user_id)`.

### Порядок миграции

1. Создать таблицу без удаления `users.tg_user_id`.
2. Для каждого существующего пользователя создать Telegram channel:

   - `channel='telegram'`;
   - `external_user_id=users.tg_user_id`;
   - `conversation_id` заполнить известным private chat ID либо тем же ID для текущей модели;
   - locale перенести из пользователя.

3. Перевести repositories и use cases на внутренний `users.id`.
4. Разрешение внешней личности выполнять только через `user_channels`.
5. Временно оставить `users.tg_user_id` как read-only compatibility field.
6. Добавить проверку соответствия legacy поля и `user_channels`.
7. После миграции всех callers прекратить запись `tg_user_id`.
8. Удалить legacy поле отдельной поздней migration после pilot.

Критерий завершения: digest, plan и astro services работают только с внутренним `user_id`; Telegram identity используется исключительно адаптером.

---

## 6. Этап 2 — Выделить общие application use cases

Создать channel-neutral use cases:

1. `StartOnboarding`.
2. `ContinueOnboarding`.
3. `HandleOnboardingAction`.
4. `GenerateDailyDigest`.
5. `UpdatePreferences`.
6. `UpdateBirthData`.
7. `ResolveCurrentPlan`.
8. `CheckFeatureEntitlement`.
9. `SubmitFeedback`.
10. `ScheduleDelivery`.
11. `PrepareOutboundDelivery`.
12. `SetDeliveryState`.

Каждый use case:

- принимает primitives/application DTO;
- получает `user_id` или `user_channel_id`;
- не принимает FastAPI Request, Telegram update или `chat_id`;
- возвращает domain result или `OutboundMessage`;
- не вызывает Telegram API напрямую;
- определяет одну transaction boundary.

Сначала обернуть существующую логику use cases, затем постепенно переносить её из 2038-строчного Telegram router.

Критерий завершения: use cases тестируются через fake repositories и `FakeMessagingChannel` без FastAPI/Telegram.

---

## 7. Этап 3 — Исправить API security boundary

1. Добавить обязательные production settings:

   - `TELEGRAM_WEBHOOK_SECRET`;
   - `INTERNAL_SERVICE_TOKEN`;
   - `ADMIN_CLI_ACTOR`;
   - trusted hosts;
   - `APP_ENV=production`;
   - `ENABLE_INTERNAL_API=false`;
   - `SCHEDULED_DELIVERY_ENABLED=false`.

2. Запрещать production startup при:

   - стандартном DB password;
   - отсутствующем webhook secret;
   - отсутствующем service token при включённом internal API;
   - `DEBUG=true`.

3. В production регистрировать публично только:

   - `POST /telegram/webhook`;
   - `GET /health`.

4. `/health` возвращает только общий статус без DB counts, version secrets или внутренних ошибок.
5. DB readiness оставить private platform probe.
6. Не регистрировать публично:

   - prefs;
   - birth;
   - summary;
   - modules;
   - alerts;
   - calendar;
   - events;
   - feedback;
   - preview;
   - metrics;
   - docs/OpenAPI.

7. Нужные служебные routes перенести под `/internal/v1`, включать отдельным flag и защищать:

   - constant-time Bearer token validation;
   - private ingress;
   - role/scope checks;
   - audit logs.

8. Не создавать публичный admin API.
9. Зарезервировать пакет/router namespace `/api/v1` для будущего authenticated PWA/Web API, но не монтировать его в pilot.
10. Удалить выдачу `str(exc)` и внутренних exception names клиенту.

Критерий завершения: black-box production test видит только `/health` и webhook; остальные routes возвращают `404`.

---

## 8. Этап 4 — Реализовать Telegram adapter и transactional outbox

### Webhook

1. Проверить `X-Telegram-Bot-Api-Secret-Token` до обработки body.
2. Выполнить только лёгкий Telegram parsing:

   - извлечь `update_id`;
   - построить `ChannelIdentity`;
   - преобразовать update в `InboundMessage`;
   - определить callback interaction ID.

3. В одной DB-транзакции:

   - создать/найти `user_channels`;
   - вставить `telegram_updates`;
   - вставить `outbox_jobs` с dedupe key `telegram:update:{update_id}`.

4. Если `update_id` уже существует, не добавлять job и вернуть `200`.
5. Вернуть `200` сразу после commit, до geocoding, digest, LLM и Telegram API calls.
6. Не выполнять бизнес-логику через FastAPI background task.

### `outbox_jobs`

Добавить поля:

- `id`;
- `job_type`;
- `channel`;
- `user_channel_id`;
- `dedupe_key`;
- `payload JSONB`;
- `priority`;
- `status`;
- `attempt_count`;
- `max_attempts`;
- `available_at`;
- `locked_at`;
- `processed_at`;
- `last_error`;
- timestamps.

Запретить хранение Telegram `chat_id` как общего job identifier. Он разрешён только внутри Telegram adapter metadata/repository.

### Worker

1. Выбирать jobs через `FOR UPDATE SKIP LOCKED`.
2. Обрабатывать job types:

   - `process_inbound_message`;
   - `send_outbound_message`;
   - `generate_scheduled_digest`;
   - `send_scheduled_digest`.

3. Для callback сначала вызвать channel-neutral acknowledgement port, затем domain mutation.
4. Domain mutation и создание outbound job выполнять в одной транзакции.
5. Retry intervals: 1, 5, 15 и 60 минут.
6. После пятой ошибки переводить job в `dead_letter`.
7. Retryable errors: timeout, rate limit, provider 5xx, временная DB/network ошибка.
8. Validation, forbidden user и некорректное semantic action считать non-retryable.
9. Добавить dead-letter metrics и административную CLI-команду безопасного retry.
10. Не обещать exactly-once внешнюю отправку. Гарантировать идемпотентность mutations и dedupe outbound jobs.

### State commands

Заменить toggle-поведение:

- snooze всегда записывает snoozed/quiet state;
- resume всегда записывает active state;
- enable delivery всегда записывает `true`;
- disable delivery всегда записывает `false`.

Критерий завершения: двойной replay `/snooze` создаёт один inbound job, один outbound job и оставляет пользователя в snoozed state.

---

## 9. Этап 5 — Исправить onboarding

1. Перенести onboarding state machine в application/domain слой.
2. Использовать состояния:

   - `age_gate_pending`;
   - `disclaimer_pending`;
   - `birth_consent_pending`;
   - `ask_birth_date`;
   - `ask_birth_time`;
   - `ask_birth_place`;
   - `confirm_birth_place`;
   - `resolve_dst_ambiguity`;
   - `ask_prefs_topics`;
   - `ask_prefs_delivery`;
   - `complete`.

3. Не объединять age, disclaimer и birth consent в один callback.
4. При age decline:

   - остановить onboarding;
   - отключить delivery;
   - не сохранять birth data.

5. `/today`/`GenerateDailyDigest` разрешать только при:

   - complete onboarding;
   - необходимых consent timestamps;
   - валидной timezone;
   - достаточных birth data.

6. Telegram adapter отвечает только за:

   - callback buttons;
   - Markdown;
   - parse Telegram location;
   - mapping callback data → semantic action;
   - отправку `OutboundMessage`.

7. Domain возвращает semantic actions, например:

   - `onboarding.age.accept`;
   - `onboarding.disclaimer.accept`;
   - `onboarding.birth_consent.accept`;
   - `delivery.snooze`;
   - `delivery.resume`.

8. Для существующих pilot/test users выполнить re-consent либо удалить тестовые профили перед production.

Критерий завершения: одна state machine проходит через Telegram и `FakeMessagingChannel` без изменения application logic.

---

## 10. Этап 6 — Исправить plans и entitlements

### Канонический контракт

1. Оставить один plan service.
2. Удалить duplicate readers и устаревшие комментарии.
3. Сохранить default plan без entitlement: `demo`.
4. Разделить интерфейсы:

   - `get_user_plan_code()`;
   - `get_plan_config()`;
   - `resolve_digest_policy()`;
   - `plan_allows_feature()`.

### Матрица cap

| План | requested short | requested medium | requested long |
|---|---|---|---|
| demo | short / 2 | short / 2 | short / 2 |
| daily | short / 2 | medium / 3 | medium / 3 |
| full | short / 2 | medium / 3 | long / 6 |
| internal | short / 2 | medium / 3 | long / 6 |

Все channel adapters, use cases, scheduler и direct service callers используют одну resolved policy.

### Схема entitlement

1. Сохранить таблицу `entitlements`.
2. Канонические поля:

   - `plan`;
   - `active`;
   - `started_at`;
   - `expires_at`.

3. Добавить:

   - plan check constraint;
   - `expires_at > started_at`;
   - partial unique index на одну `active=true` строку;
   - `source`;
   - `created_by`;
   - `reason`;
   - `updated_at`.

4. Нормализовать aliases:

   - `basic→daily`;
   - `pro→full`;
   - `free→daily`;
   - `premium→full`.

5. Feature gates всегда учитывают active/time window.
6. Удалить bypass «нет entitlement — пропустить проверку».

### Audit-logged admin CLI

Добавить команды:

- `entitlements show`;
- `entitlements assign`;
- `entitlements revoke`;
- `entitlements history`.

`assign` должен:

1. Идентифицировать пользователя через `channel + external_user_id` или внутренний user ID.
2. Поддерживать `--dry-run`, который показывает before/after и не изменяет БД.
3. Для записи требовать `--actor`, `--reason` и уникальный operation ID.
4. Валидировать plan code, `started_at` и `expires_at`.
5. Заблокировать user row через `SELECT ... FOR UPDATE`.
6. Деактивировать текущий active entitlement.
7. Вставить новый entitlement.
8. Проверить effective plan.
9. Записать immutable audit event с before/after.
10. Commit выполнить одной транзакцией.
11. При повторе operation ID вернуть исходный результат без новой mutation.
12. Не выводить credentials, tokens, DSN или другие secrets.

CLI запускается только как private one-off admin job с managed DB credentials. Публичного endpoint и инструкции с прямым SQL не создавать.

Критерий завершения: DB запрещает два active entitlement; concurrency test
подтверждает row-lock behavior; dry-run не изменяет данные; idempotent retry не
создаёт повторную запись; каждое назначение имеет actor, reason и before/after
audit; CLI output не раскрывает secrets.

---

## 11. Этап 7 — Исправить Alembic и схему БД

Исторические revisions не редактировать. Использовать corrective forward migrations.

1. Выбрать `modules_registry` канонической таблицей.
2. Идемпотентно перенести данные из `module_registry`.
3. Удалить singular-таблицу после проверки.
4. Согласовать `LLMUsageLog`:

   - ID — `BigInteger`;
   - cost — `Numeric(10,6)`/`Decimal`.

5. Отразить migration-created indexes в ORM metadata.
6. Сделать seed downgrade безопасным для dev/test данных.
7. Production rollback оформить как image rollback + forward fix.
8. Добавить:

    - clean upgrade test;
    - snapshot upgrade test;
    - `alembic check`;
    - constraint tests;
    - migration data verification.

Ownership соседних schema changes:

- `user_channels` реализуется только в B1;
- `telegram_updates`, `outbox_jobs` и `telegram_deliveries` реализуются только
  в B4;
- canonical event identity и event uniqueness реализуются только в B9;
- A7.* не создаёт эти таблицы и constraints.

Критерий завершения: `alembic check` не показывает drift, production-like snapshot обновляется без потерь.

---

## 12. Этап 8 — Исправить timezone, geocoding и profile updates

1. Использовать только aware UTC: `datetime.now(timezone.utc)`.
2. Все timezone conversions выполнять через `zoneinfo`.
3. Реализовать настоящую PATCH-семантику:

   - omitted поля сохраняются;
   - изменение времени не стирает place/lat/lon/tz;
   - изменение места запускает новый geocoding;
   - derived state инвалидируется после commit.

4. Добавить DST fold:

   - nonexistent local time отклоняется;
   - ambiguous time требует выбора offset;
   - выбор сохраняется.

   Wave A реализует domain/service detection, validation и результат выбора.
   Telegram prompts/buttons для выбора offset реализуются только в B5.

5. Удалить production fallback страна→столица/New York.
6. Не назначать UTC при неизвестном месте.
7. Geocoder возвращает кандидата с координатами, display name и timezone.
8. Wave A реализует domain/service candidate and confirmation contract.
   Telegram confirmation UI и callback mapping реализуются только в B5.
9. Domain/service возвращает явный unresolved result вместо silent fallback;
   перевод onboarding в blocking state выполняется в B5.
10. Добавить Nominatim User-Agent, rate limit и retry/backoff.
11. Удалить PII/debug file logging.

Критерий завершения: birth time edit сохраняет geo; неизвестное место не превращается в UTC; DST cases имеют детерминированный результат.

---

## 13. Этап 9 — Исправить digest cache, events и RAG

### Pilot scope

1. Сделать cache correctness-safe:

   - отключить небезопасное cross-request reuse для `/today`;
   - не добавлять persistent digest history на pilot;
   - не добавлять Redis;
   - изменение plan, locale, interests, timezone или birth data не должно
     возвращать старый digest.

2. Выбрать `events` каноническим event store.
3. Добавить детерминированный `event_key` и DB uniqueness.
4. Перевести live generation и batch precompute на один repository и устранить
   insert-if-empty race.
5. Добавить versioned idempotent production content seed и отдельный deploy
   seed job.
6. Добавить CI inventory gate для RU/EN/ES, trigger/persona coverage,
   long-copy coverage, manifest version и checksum.
7. Удалить test atoms из всех production selection paths.
8. Заменить user-facing moon-phase stub реальным вычислением.
9. Сделать ranking и tie-breaking детерминированными: score, priority, atom ID.
10. Локализовать disclaimer и не заявлять Houses/ASC/MC до golden
    verification.

### Post-pilot scope

1. Добавить persistent `digest_runs` с уникальностью
   `(user_id, local_date, input_hash)`.
2. Включить в fingerprint effective entitlement, final length, locale,
   interests, timezone, birth signature, local date, content version и
   renderer version.
3. Сохранять selected atom IDs как content history.
4. Добавить seven-day atom cooldown при наличии детерминированной альтернативы.
5. Миграцию legacy calendar events выполнять в TC11, а не в pilot B9.

Критерий завершения pilot: изменение digest inputs не возвращает старый
результат; параллельные вычисления не создают duplicate events; чистый deploy
содержит production content без test atoms; user-facing moon phase реальна;
ranking детерминирован.

---

## 14. Этап 10 — Исправить scheduler и delivery worker

1. Managed scheduler запускает channel-neutral enqueue command каждую минуту.
2. Scheduler не отправляет сообщения напрямую.
3. Он создаёт `generate_scheduled_digest` jobs с:

   - `channel`;
   - `user_channel_id`;
   - local date;
   - delivery kind;
   - dedupe key.

4. Worker выбирает due users по их timezone и local delivery time.
5. Проверяет:

   - onboarding complete;
   - consent;
   - channel active;
   - delivery enabled;
   - quiet mode/hours;
   - current plan policy.

6. Использует `resolve_digest_policy`; ошибка `.code` у строки устраняется.
7. Создаёт `telegram_deliveries` до отправки.
8. Unique constraint не позволяет вторую Telegram delivery за ту же local date/kind.
9. Outbound job остаётся channel-neutral; Telegram adapter выполняет provider call.
10. `SCHEDULED_DELIVERY_ENABLED=false` остаётся production default до полного тестирования.
11. Rollout:

    - internal users;
    - закрытая тестовая когорта;
    - 10% pilot;
    - 100% после 24 часов без duplicate/missed delivery.

Критерий завершения: worker применяет caps 2/3/6, учитывает local time и не отправляет второй digest за дату.

---

## 15. Этап 11 — Calendar после pilot

Calendar не является blocker первого pilot: production router его не регистрирует.

После стабилизации Telegram:

1. Добавить `calendar_subscriptions`.
2. Генерировать 256-bit opaque token.
3. Хранить только token hash.
4. Добавить revoke/rotation.
5. Не принимать `user_id` или произвольную timezone.
6. Проверять Full/Internal entitlement при каждом чтении.
7. Строить `.ics` только из канонических `events`.
8. Возвращать `404` для invalid/revoked/not-entitled token.
9. Редактировать token в access logs.
10. Включать endpoint отдельным production flag.

Критерий включения: signed-token, plan-gate и canonical-event tests проходят; endpoint проверен на internal accounts.

---

## 16. Этап 12 — Logging, privacy и observability

1. Удалить direct file logging и debug instrumentation.
2. Писать structured JSON в stdout.
3. Добавлять:

   - request ID;
   - update ID;
   - outbox job ID;
   - user channel ID;
   - delivery ID.

4. Не логировать:

   - bot/API/calendar tokens;
   - raw birth place;
   - coordinates;
   - полный Telegram payload;
   - полные prefs;
   - birth data.

5. Raw Telegram payload хранить максимум 7 дней.
6. Dead-letter metadata хранить 30 дней.
7. Добавить user export/delete use cases, не привязанные к Telegram.
8. `/metrics` разрешить только private scraper с service authentication.
9. Добавить alerts:

   - webhook p95 >200 ms;
   - oldest outbox job >2 минут;
   - worker failure rate >1%;
   - dead-letter growth;
   - 5xx >1%;
   - backup/restore failure;
   - LLM budget exceed.

Критерий завершения: PII/secret log scan чистый, а каждая job прослеживается по correlation IDs.

---

## 17. Этап 13 — Production container, CI/CD и recovery

### Production runtime

1. Создать один immutable image для web, worker, scheduler CLI и migration jobs.
2. Использовать разные container commands, но один image digest.
3. Запускать от non-root пользователя.
4. Не использовать bind mounts.
5. Включить ephemeris в image.
6. Проверять его SHA-256 при build/startup.
7. Закрепить dependency versions и hashes.
8. Использовать working image-native healthcheck.
9. Размещать web, worker и managed PostgreSQL в одном регионе.
10. PostgreSQL доступен только через private network и TLS.
11. HTTPS завершается managed ingress.
12. Kubernetes manifests не создавать.

### CI

Добавить обязательные jobs:

- pre-commit;
- существующие и новые pytest;
- clean Alembic upgrade;
- `alembic check`;
- production-like snapshot upgrade;
- content seed/inventory;
- architecture import-boundary tests;
- production image build;
- non-root/health smoke;
- dependency/image/secret scans;
- SBOM.

### CD

1. Проверить последний backup.
2. Создать pre-deploy snapshot.
3. Запустить migration job.
4. Запустить content seed job.
5. Развернуть web с scheduled delivery disabled.
6. Развернуть один worker.
7. Выполнить smoke.
8. Зарегистрировать Telegram webhook с secret token.
9. Проверить duplicate update и callback acknowledgement.
10. Scheduled delivery включать только по отдельному rollout.

### Backup и restore

- PITR: RPO не более 5 минут;
- daily snapshots;
- retention 14 дней;
- шифрование;
- restore drill ежеквартально;
- RTO не более 2 часов.

Production rollback:

- выключить scheduler/delivery;
- вернуть предыдущий image digest;
- применить forward-fix migration при несовместимости;
- restore DB использовать только при подтверждённой порче данных.

Критерий завершения: один и тот же image digest проходит staging и production, restore drill подтверждён.

---

## 18. Этап 14 — P2 cleanup и документация

1. Разделить Telegram router на parser, renderer, adapter и registration.
2. Удалить duplicate plan readers.
3. Удалить deprecated geo implementations.
4. Удалить `Old_version_daily_digest_service.py`.
5. Устранить broad exception handling.
6. Оставить один root route.
7. Разделить feedback, product events и operational audit.
8. Обновить README:

   - локальный запуск;
   - архитектурные слои;
   - environment matrix;
   - migrations;
   - content seed;
   - tests;
   - worker/scheduler.

9. Добавить runbooks:

   - deploy/rollback;
   - backup/restore;
   - admin CLI тарифов;
   - webhook secret rotation;
   - dead-letter recovery;
   - failed migration;
   - privacy export/delete;
   - incidents.

10. Добавить руководство по новому channel adapter:

    - реализовать parser;
    - реализовать renderer;
    - реализовать `MessagingChannel`;
    - зарегистрировать channel;
    - не менять domain, plans, RAG или astro core.

Критерий завершения: тестовый второй channel adapter подключается без изменений core/application logic.

---

## 19. Обязательный test plan

Перед повторным GO/NO-GO review должны пройти:

1. Все существующие 100 тестов.
2. Architecture import-boundary tests.
3. Backfill `users.tg_user_id → user_channels`.
4. Unique `(channel, external_user_id)`.
5. Fake channel end-to-end digest.
6. Telegram parser/renderer contract tests.
7. Missing/wrong/valid webhook secret.
8. Duplicate `update_id`.
9. Duplicate outbox `dedupe_key`.
10. Replay snooze/resume без toggle.
11. Callback acknowledgement перед mutation.
12. Outbox retry/backoff/dead-letter.
13. Worker crash/restart.
14. Plan matrix demo/daily/full/internal.
15. No/future/active/expired/revoked entitlement.
16. Admin CLI assign/revoke/history и audit record.
17. Calendar/alerts disabled в pilot production.
18. Полный onboarding EN/ES/RU.
19. Birth partial updates и DST cases.
20. Cache fingerprint после plan/language/interests/timezone/birth.
21. Concurrent event/digest generation.
22. Idempotent content seed.
23. Реальные moon phase golden cases.
24. Local-time scheduled delivery.
25. Quiet/onboarding/consent delivery gates.
26. Clean migration, snapshot upgrade и `alembic check`.
27. Production route exposure test.
28. Non-root/self-contained image smoke.
29. Backup/restore drill.
30. Staging test с реальным Telegram test bot.
31. Proof test: второй fake channel подключается без изменения plans, RAG, digest или astro core.

---

## 20. Production GO/NO-GO

Production pilot получает **GO**, только если:

- закрыты все P0;
- public route exposure соответствует trust boundary;
- webhook secret и idempotency подтверждены;
- plans и caps применяются единообразно;
- Alembic не имеет drift;
- production content загружается автоматически;
- Telegram полностью вынесен в adapter;
- domain/application проходят import-boundary tests;
- worker устойчив к replay/retry;
- production image immutable, healthy и non-root;
- backup и restore подтверждены;
- scheduled delivery остаётся выключенным до отдельного допуска;
- calendar endpoint отсутствует в pilot production.

## 21. Явные ограничения

- Публичного web/mobile API в первом pilot нет.
- `/api/v1` только архитектурно зарезервирован.
- Calendar отложен до post-pilot.
- WhatsApp и Viber не реализуются сейчас, но должны подключаться как adapters.
- Микросервисы и Kubernetes не вводятся.
- Redis не вводится.
- Очередь и locking реализуются через PostgreSQL.
- Production использует один web instance и один worker.
- Тарифы назначаются только audit-logged admin CLI.
- Прямые SQL-инструкции для назначения тарифов не являются поддерживаемой операционной процедурой.
- Default plan без entitlement остаётся `demo`.

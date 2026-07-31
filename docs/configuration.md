# Application configuration

Issue [#35](https://github.com/smytsyk-beep/a_daily/issues/35) defines the
canonical runtime settings contract. Settings are parsed once by
`common.config.Settings`; the application imports that validated singleton
before it imports or registers routes. Validation never connects to PostgreSQL,
Telegram, or another provider.

## Environments

`APP_ENV` accepts only `dev`, `test`, or `prod`. Leading/trailing whitespace and
letter case are normalized, so `APP_ENV=" Prod "` becomes `prod`. Every other
value fails settings parsing. The environment is never inferred from a
hostname, CI, credentials, or another indirect signal.

`dev` is the safe local default. `dev` and `test` may use the local database
defaults, omit Telegram credentials, enable debug mode, and explicitly enable
scheduled delivery for isolated tests. Their default trusted hosts are
`localhost,127.0.0.1`.

## HTTP route registration

The canonical `app.main:create_app` factory selects routes only from `APP_ENV`.
`DEBUG` controls FastAPI debug behavior in `dev` and `test`; it never expands or
reduces the route inventory.

For `APP_ENV=prod`, the public pilot application registers exactly:

- `GET /health`;
- `POST /telegram/webhook`.

Production sets `docs_url`, `redoc_url`, and `openapi_url` to `None` and forces
FastAPI debug mode off. Root, database health, metrics, preview, events,
feedback, module, user, birth-data, calendar, internal, admin, and future PWA
routes are not registered. They are physically absent rather than hidden by
middleware or an authorization dependency.

For `APP_ENV=dev` and `APP_ENV=test`, the existing development routes, root,
Swagger UI, Redoc, and OpenAPI remain registered. This broader surface is for
local development and automated tests only; it is not the pilot production API.

`GET /health` uses the same coarse response in every environment:

```json
{"status": "ok"}
```

It does not report the environment, application name or version, database
state, dependency inventory, configuration, or exception details. Database
readiness remains separate at `/db/health` in non-production and is not a
public pilot route. Telegram secret-header verification and webhook
idempotency remain later B4 work; route registration does not claim those
controls.

`prod` fails closed before route registration or provider access. It requires:

- `DEBUG=false`;
- a non-empty, non-placeholder `TELEGRAM_BOT_TOKEN`;
- a non-placeholder `TELEGRAM_WEBHOOK_SECRET` containing 32–256 ASCII letters,
  digits, underscores, or hyphens;
- explicit `TRUSTED_HOSTS`;
- a non-empty database password that is neither `astrodaily` nor the template
  placeholder;
- `SCHEDULED_DELIVERY_ENABLED=false` for the current pilot;
- `INTERNAL_SERVICE_TOKEN` only when `ENABLE_INTERNAL_API=true`.

Stripe credentials are not part of the pilot production startup contract.

## Database precedence

When non-empty, `DATABASE_URL` overrides every `POSTGRES_*` field. Production
validation parses it with SQLAlchemy's URL parser, requires a PostgreSQL URL
with host, database, and password, and checks the decoded effective password.
It does not split credentials manually and does not open a connection.

When `DATABASE_URL` is empty or absent, the effective URL is constructed with
SQLAlchemy's URL builder from `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`,
`POSTGRES_USER`, and `POSTGRES_PASSWORD`. This safely percent-encodes
credentials. Existing callers continue to use `settings.DATABASE_URL`.

Neither a DSN nor any part of it is included in validation errors.

## Trusted hosts

`TRUSTED_HOSTS` uses one comma-separated format:

```text
TRUSTED_HOSTS=api.example.com,*.services.example.com
```

Entries are trimmed and normalized to lowercase. Exact hostnames and leading
wildcard subdomain patterns are accepted. An empty list, the unrestricted `*`,
a URL scheme, path, port, malformed label, or ambiguous value is rejected in
production. The normalized runtime value is available as
`settings.TRUSTED_HOSTS`, a tuple ready for the middleware work owned by Issue
#37. Issue #35 does not add that middleware.

## Pilot flags

`ENABLE_INTERNAL_API` defaults to `false` in every environment. Setting it to
`true` in production requires a non-placeholder `INTERNAL_SERVICE_TOKEN`, but
does not register internal routes. The post-pilot internal API remains owned by
tracking Issue #28.

`SCHEDULED_DELIVERY_ENABLED` also defaults to `false`. `prod` rejects `true`
until a separate scheduled-delivery release gate changes the contract. `dev`
and `test` may enable it for isolated test scenarios. This setting does not
start a scheduler or worker.

## Safe failure contract

Cross-field production failures raise `UnsafeProductionConfiguration`. Its
message contains only the following deterministic rule codes:

- `debug_enabled`;
- `telegram_bot_token_missing`;
- `telegram_bot_token_placeholder`;
- `telegram_webhook_secret_missing`;
- `telegram_webhook_secret_placeholder`;
- `telegram_webhook_secret_invalid`;
- `database_url_invalid`;
- `database_password_missing`;
- `database_password_unsafe`;
- `trusted_hosts_missing`;
- `trusted_hosts_wildcard`;
- `trusted_hosts_invalid`;
- `internal_service_token_missing`;
- `internal_service_token_placeholder`;
- `scheduled_delivery_enabled`.

Declarative type and enum failures raise `SettingsConfigurationError` with a
safe `<field>_invalid` code, such as `app_env_invalid`, `debug_invalid`, or
`postgres_port_invalid`. Pydantic input rendering is disabled. Exception text,
exception repr, captured logs, and settings repr do not contain secret values,
passwords, service tokens, or DSNs.

## Examples

Safe local development can use non-secret defaults:

```text
APP_ENV=dev
DEBUG=true
TRUSTED_HOSTS=localhost,127.0.0.1
ENABLE_INTERNAL_API=false
SCHEDULED_DELIVERY_ENABLED=false
```

A production deployment supplies real values through its managed secret store,
not source control:

```text
APP_ENV=prod
DEBUG=false
DATABASE_URL=REPLACE_WITH_MANAGED_DATABASE_URL
TELEGRAM_BOT_TOKEN=REPLACE_WITH_PRODUCTION_TELEGRAM_BOT_TOKEN
TELEGRAM_WEBHOOK_SECRET=REPLACE_WITH_PRODUCTION_TELEGRAM_WEBHOOK_SECRET
TRUSTED_HOSTS=app.example.invalid
ENABLE_INTERNAL_API=false
SCHEDULED_DELIVERY_ENABLED=false
```

The production example is intentionally non-runnable. Do not paste real values
into documentation, command output, issue comments, or logs.

## Troubleshooting

Read only the reported violation codes and correct the named setting through
the deployment secret/configuration system. Do not print the settings object,
DSN, environment, or secret value to diagnose a startup failure. A type error
means the environment value cannot be parsed as the declared setting type; a
production rule code means parsing succeeded but the effective combination is
unsafe.

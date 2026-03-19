# Rating Service MVP

Backend, landing page и production docs для `Wobbly`.

Сейчас проект включает:
- API для anonymous auth, профиля и рейтингов
- admin API и admin UI foundation
- landing page на `https://wobbly.site`
- текстовую docs page на `https://api.wobbly.site/api/docs`
- production deploy через GitHub Actions

## Стек

- FastAPI
- PostgreSQL
- Docker Compose для локальной разработки
- systemd + nginx в production
- GitHub Actions для CI/CD

## Project Structure

Текущая структура проекта после второго этапа рефакторинга:
- `app/main.py` — минимальный entrypoint
- `app/api/app.py` — app factory
- `app/api/dependencies.py` — общие dependencies
- `app/api/routes/` — route modules по зонам ответственности
- `app/core/` — auth, config, rate limiting
- `app/db/` — database access и init_db
- `app/domain/` — Pydantic schemas
- `app/services/` — business logic
- `app/static/` — landing, docs page, css, js, assets
- `alembic/` — migration scripts
- `scripts/` — CI checks, deploy, docs sync checks
- `.githooks/` — локальные git hooks
- `tests/` — unit и integration tests
- `docs/` — operational, mobile, roadmap и handoff документация
- `.github/workflows/pipeline.yml` — verify + deploy pipeline
- `pyproject.toml` — lint/test tooling config

Старые модули:
- `app/auth.py`
- `app/config.py`
- `app/database.py`
- `app/rate_limit.py`
- `app/schemas.py`

пока оставлены как compatibility wrappers, чтобы рефакторинг был безопасным и не ломал imports одним шагом.

## Current Project Snapshot

Если работа переносится в новый чат, это нужно считать актуальной базой проекта:
- production API: `https://api.wobbly.site`
- production Swagger: `https://api.wobbly.site/api/swagger`
- production text docs: `https://api.wobbly.site/api/docs`
- production site: `https://wobbly.site`
- staging API path on server: `/opt/rating-service-staging`
- staging service: `rating-service-staging.service`
- staging database: `app_staging`
- staging public URL: `https://staging-api.wobbly.site`
- staging workflow: `.github/workflows/staging.yml` on `develop`
- продовый сервис: `rating-service.service`
- продовый путь на сервере: `/opt/rating-service`
- reverse proxy в production: `nginx`
- базовый edge-side rate limiting уже включен на `api.wobbly.site`
- основной путь разработки: feature branch -> merge в `develop` -> staging pipeline
- `main` не трогаем по умолчанию; merge `develop` -> `main` делаем только по явной команде на production release
- production release path: merge `develop` -> `main` -> production pipeline
- staging deploy path: push в `develop` -> GitHub Actions -> verify -> deploy-staging
- ручной deploy через копирование файлов в `/opt/rating-service` и `systemctl restart rating-service` остается fallback-сценарием

Это важно:
- локальный `docker compose` нужен для разработки
- production topology уже другая, и ее не нужно заново угадывать
- точные команды деплоя описаны в `docs/DEPLOY.md`
- отдельная сводка для переноса контекста лежит в `docs/HANDOFF.md`
- staging уже поднят на `https://staging-api.wobbly.site` и закрыт через `X-Staging-Key`
- админка спроектирована под `https://admin.wobbly.site/production/` и `https://admin.wobbly.site/staging/`
- первый `owner` bootstrap'ится через env:
  - `ADMIN_BOOTSTRAP_LOGIN`
  - `ADMIN_BOOTSTRAP_PASSWORD`

## API

### `POST /auth/anonymous`

Создает анонимного пользователя и возвращает bearer token.

Response:

```json
{
  "userId": 15,
  "accessToken": "rt_xxxxx",
  "tokenType": "bearer"
}
```

После этого токен надо передавать в заголовке:

```http
Authorization: Bearer rt_xxxxx
```

### `GET /me`

Возвращает профиль текущего авторизованного пользователя.

### `PATCH /me/profile`

Request:

```json
{
  "username": "player_1",
  "participateInRating": true
}
```

Responses:
- `200` профиль обновлён
- `401` не передан или невалиден bearer token
- `409` такой `username` уже существует
- `422` нельзя включить участие в рейтинге без `username`

### `PATCH /me/rating`

Позволяет отдельно включить или выключить участие текущего пользователя в рейтингах.

Request:

```json
{
  "participateInRating": true
}
```

Responses:
- `200` участие в рейтинге обновлено
- `401` не передан или невалиден bearer token
- `422` нельзя включить участие в рейтинге без `username`

### `POST /me/score`

Request:

```json
{
  "score": 42
}
```

Responses:
- `200` рейтинг обновлён
- `401` не передан или невалиден bearer token
- `429` слишком много обновлений рейтинга

## Error Contract

Ошибки API теперь возвращаются в едином формате:

```json
{
  "code": "USERNAME_ALREADY_EXISTS",
  "message": "Username already exists"
}
```

Основные коды:
- `MISSING_AUTHORIZATION_HEADER` — в запросе отсутствует заголовок `Authorization: Bearer <accessToken>`
- `INVALID_AUTHORIZATION_HEADER` — заголовок `Authorization` передан в неправильном формате
- `INVALID_TOKEN` — токен передан, но не найден в системе или больше невалиден
- `USERNAME_ALREADY_EXISTS` — такое имя уже занято другим пользователем
- `USERNAME_REQUIRED_FOR_RATING` — нельзя включить участие в рейтинге без `username`
- `USER_NOT_FOUND` — пользователь не найден по переданным данным
- `RATE_LIMIT_EXCEEDED` — превышен лимит запросов, нужно повторить позже
- `VALIDATION_ERROR` — тело запроса не прошло валидацию: не хватает полей или формат данных неверный
- `INTERNAL_SERVER_ERROR` — внутренняя ошибка backend

### `GET /leaderboard/top?limit=100`

Возвращает пользователей с максимальным рейтингом, у которых `score >= 0`.

### `GET /leaderboard/bottom?limit=100`

Возвращает пользователей с минимальным рейтингом, у которых `score < 0`.

Подробный мобильный контракт:
- `docs/MOBILE_API.md`
- `https://api.wobbly.site/api/docs`

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска API будет доступно на:
- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`

## Что ещё можно улучшить

- усилить integration tests сценариями с тестовой БД
- добавить readiness endpoint
- добавить structured logging
- добавить fail2ban или Cloudflare как следующий anti-abuse слой

## Development

- workflow: `docs/DEVELOPMENT_WORKFLOW.md`
- production/deploy: `docs/DEPLOY.md`
- database access: `docs/DB_ACCESS.md`
- handoff summary: `docs/HANDOFF.md`
- anti-abuse plan: `docs/ANTI_ABUSE.md`
- backend roadmap: `docs/BACKEND_ROADMAP.md`
- conventions: trunk-based development + Conventional Commits
- branch flow: `develop` для активной разработки, `main` только для production releases по явному запросу
- если меняется API, нужно обновлять текстовую docs page на `https://api.wobbly.site/api/docs` в том же изменении
- CI дополнительно проверяет, что API-изменения не уходят без обновления `/api/docs`
- linters and tests: `ruff`, `pytest`
- локальные обязательные hooks: `.githooks/pre-commit`, `.githooks/pre-push`
- после рефакторинга новые endpoint changes обычно живут в `app/api/routes/`, `app/services/`, `app/domain/`, `app/core/`
- schema changes теперь должны идти через Alembic migrations

Если меняется поведение API, обычно нужно обновлять:
- `app/static/js/api-docs.js`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

Чтобы включить локальные hooks:

```bash
./scripts/install_git_hooks.sh
```

Что делают hooks:
- `pre-commit` — `ruff --fix`, `ruff`, Python syntax, JS syntax
- `pre-push` — `pytest`

## Context Transfer

Если работа переносится в новый чат, новый чат должен сначала прочитать:
- `docs/HANDOFF.md`
- `README.md`
- `docs/BACKEND_ROADMAP.md`
- `docs/MOBILE_API.md`
- `docs/DEPLOY.md`
- `docs/DEVELOPMENT_WORKFLOW.md`

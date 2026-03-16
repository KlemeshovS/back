# Rating Service MVP

Backend, landing page и production docs для `Wobbly`.

Сейчас проект включает:
- API для anonymous auth, профиля и рейтингов
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
- `scripts/` — CI checks, deploy, docs sync checks
- `.githooks/` — локальные git hooks
- `tests/` — unit и integration tests
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
- продовый сервис: `rating-service.service`
- продовый путь на сервере: `/opt/rating-service`
- reverse proxy в production: `nginx`
- основной путь деплоя: merge в `main` -> GitHub Actions -> verify -> deploy
- ручной deploy через копирование файлов в `/opt/rating-service` и `systemctl restart rating-service` остается fallback-сценарием

Это важно:
- локальный `docker compose` нужен для разработки
- production topology уже другая, и ее не нужно заново угадывать
- точные команды деплоя описаны в `DEPLOY.md`
- отдельная сводка для переноса контекста лежит в `HANDOFF.md`

## API

### `POST /auth/anonymous`

Создает анонимного пользователя и возвращает bearer token.

Response:

```json
{
  "user_id": 15,
  "access_token": "rt_xxxxx",
  "token_type": "bearer"
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
  "participate_in_rating": true
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
  "participate_in_rating": true
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

### `POST /users/register`

Legacy endpoint. Оставлен для обратной совместимости.

### `POST /users/score`

Legacy endpoint. Оставлен для обратной совместимости.

### `GET /leaderboard/top?limit=100`

Возвращает пользователей с максимальным рейтингом, у которых `score >= 0`.

### `GET /leaderboard/bottom?limit=100`

Возвращает пользователей с минимальным рейтингом, у которых `score < 0`.

Подробный мобильный контракт:
- `MOBILE_API.md`
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

- вынести миграции в Alembic
- усилить integration tests сценариями с тестовой БД
- унифицировать ошибки в формате `code` + `message`
- добавить readiness endpoint
- добавить structured logging

## Development

- workflow: `DEVELOPMENT_WORKFLOW.md`
- production/deploy: `DEPLOY.md`
- handoff summary: `HANDOFF.md`
- conventions: trunk-based development + Conventional Commits
- если меняется API, нужно обновлять текстовую docs page на `https://api.wobbly.site/api/docs` в том же изменении
- CI дополнительно проверяет, что API-изменения не уходят без обновления `/api/docs`
- linters and tests: `ruff`, `pytest`
- локальный обязательный pre-commit guard: `.githooks/pre-commit`
- после рефакторинга новые endpoint changes обычно живут в `app/api/routes/`, `app/services/`, `app/domain/`, `app/core/`

Если меняется поведение API, обычно нужно обновлять:
- `app/static/js/api-docs.js`
- при необходимости `MOBILE_API.md`
- при необходимости `README.md`

Чтобы включить локальный обязательный pre-commit hook:

```bash
./scripts/install_git_hooks.sh
```

## Context Transfer

Если работа переносится в новый чат, новый чат должен сначала прочитать:
- `HANDOFF.md`
- `README.md`
- `BACKEND_ROADMAP.md`
- `MOBILE_API.md`
- `DEPLOY.md`
- `DEVELOPMENT_WORKFLOW.md`

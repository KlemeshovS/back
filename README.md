# Rating Service MVP

Простой backend для:
- регистрации уникального `username`
- сохранения рейтинга для пользователя
- выдачи `top 100` и `anti-top 100`

## Стек

- FastAPI
- PostgreSQL
- Docker Compose

## Project Structure

Текущая структура проекта после первой фазы рефакторинга:
- `app/main.py` — FastAPI entrypoint и маршруты
- `app/core/` — auth, config, rate limiting
- `app/db/` — database access и init_db
- `app/domain/` — Pydantic schemas
- `app/static/` — landing, docs page, css, js, assets
- `scripts/` — CI checks, deploy, docs sync checks
- `tests/` — unit tests
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
- основной путь деплоя теперь: merge в `main` -> GitHub Actions -> проверки -> deploy на production
- ручной deploy через копирование файлов в `/opt/rating-service` и `systemctl restart rating-service` остается как fallback

Это важно:
- локальный `docker compose` нужен для разработки
- production topology уже другая, и ее не нужно заново угадывать
- точные команды деплоя описаны в `DEPLOY.md`

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

Request:

```json
{
  "username": "player_1"
}
```

Responses:
- `201` пользователь создан
- `409` пользователь уже существует
- `429` слишком много попыток регистрации

Response:

```json
{
  "status": "created",
  "id": 1,
  "username": "player_1"
}
```

### `POST /users/score`

Legacy endpoint. Оставлен для обратной совместимости.

Request:

```json
{
  "user_id": 1,
  "score": 42
}
```

Также временно поддерживается старый формат:

```json
{
  "username": "player_1",
  "score": 42
}
```

Responses:
- `200` рейтинг обновлён
- `404` пользователь не найден
- `429` слишком много обновлений рейтинга

### `GET /leaderboard/top?limit=100`

Возвращает пользователей с максимальным рейтингом, у которых `score >= 0`.

### `GET /leaderboard/bottom?limit=100`

Возвращает пользователей с минимальным рейтингом, у которых `score < 0`.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска API будет доступно на:
- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`

## Что нужно сделать руками на сервере

1. Дать SSH-доступ по ключу или паролю.
2. Завести домен или поддомен и направить DNS на сервер.
3. Создать `.env` с боевыми значениями.
4. Настроить резервные копии PostgreSQL.

## Production-запуск на сервере

Сервис можно поднять сразу по IP:

```bash
cp .env.example .env
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

С текущим `deploy/Caddyfile` Caddy слушает `:80` и проксирует в API. Это подходит для запуска по IP.

Если появится домен, замени `deploy/Caddyfile` на:

```caddy
api.example.com {
    reverse_proxy api:8000
}
```

После этого Caddy сам выпустит HTTPS-сертификат Let's Encrypt.

## Что я уже сделал

- подготовил backend
- добавил контейнеризацию
- описал API-контракт
- добавил anonymous auth через bearer token

## Что ещё можно улучшить

- вынести rate limiting в Redis или PostgreSQL для multi-instance окружения
- вынести миграции в Alembic
- добавить тесты

## Development

- workflow: `DEVELOPMENT_WORKFLOW.md`
- conventions: trunk-based development + Conventional Commits
- если меняется API, нужно обновлять текстовую docs page на `https://api.wobbly.site/api/docs` в том же изменении
- CI дополнительно проверяет, что API-изменения не уходят без обновления `/api/docs`
- linters and tests: `ruff`, `pytest`

## Context Transfer

Если работа переносится в новый чат, новый чат должен сначала прочитать:
- `README.md`
- `BACKEND_ROADMAP.md`
- `MOBILE_API.md`
- `DEPLOY.md`
- `DEVELOPMENT_WORKFLOW.md`

Перед новым анализом не надо заново выяснять:
- где находится production-код
- как называется systemd unit
- через что отдается `wobbly.site`
- через что отдается `api.wobbly.site`
- как именно сейчас делается deploy

## Mobile App

- mobile API: `MOBILE_API.md`

## Deployment

- deploy guide: `DEPLOY.md`
- GitHub Actions pipeline: `.github/workflows/pipeline.yml`

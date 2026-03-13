# Rating Service MVP

Простой backend для:
- регистрации уникального `username`
- сохранения рейтинга для пользователя
- выдачи `top 100` и `anti-top 100`

## Стек

- FastAPI
- PostgreSQL
- Docker Compose

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

Возвращает пользователей с максимальным рейтингом.

### `GET /leaderboard/bottom?limit=100`

Возвращает пользователей с минимальным рейтингом.

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска API будет доступно на:
- `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`

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

## Mobile App

- mobile API: `MOBILE_API.md`

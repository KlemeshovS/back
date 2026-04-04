# Mobile API

Production public contract для mobile-клиента.

Если нужна ручная staging-проверка, это operational detail из `develop`, а не основной контракт.

## Base URL

```text
https://api.wobbly.site/api/v1
```

Legacy unversioned routes пока остаются для обратной совместимости, но новые mobile-версии должны использовать `/api/v1/...`.

## Полезные production URLs

- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`

## Authorization

Для защищенных методов:

```http
Authorization: Bearer <accessToken>
```

Защищенные методы:
- `GET /api/v1/me`
- `PATCH /api/v1/me/profile`
- `PATCH /api/v1/me/rating`
- `POST /api/v1/me/score`

## Базовый mobile flow

### Первый запуск

1. проверить, есть ли локально `accessToken`
2. если токена нет:
   - вызвать `POST /api/v1/auth/anonymous`
   - сохранить `accessToken`
   - сохранить `userId`

### Обычный старт приложения

1. если токен есть:
   - вызвать `GET /api/v1/me`
   - получить текущий профиль

### Профиль и рейтинг

- `PATCH /api/v1/me/profile` — сохранить `username` и участие
- `PATCH /api/v1/me/rating` — отдельно включить или выключить участие
- `POST /api/v1/me/score` — обновить score

### Таблицы рейтинга

- `GET /api/v1/leaderboard/top?limit=100`
- `GET /api/v1/leaderboard/bottom?limit=100`

## Правила backend

- участие в рейтинге можно включить только если есть `username`
- `username` должен быть уникальным
- разрешены латинские буквы, цифры, `_`, `.`, `-`
- если `username` уже был сохранен, его нельзя очистить в пустое значение
- если участие выключено, пользователь может смотреть рейтинги, но не участвует
- `score` не нужно передавать вместе с `userId` или `username`

## Endpoint summary

### `POST /api/v1/auth/anonymous`

Создает anonymous user и возвращает bearer token.

### `GET /api/v1/me`

Возвращает профиль текущего пользователя.

Поля ответа:
- `id`
- `username`
- `participateInRating`

### `PATCH /api/v1/me/profile`

Сохраняет `username` и `participateInRating`.

### `PATCH /api/v1/me/rating`

Отдельно включает или выключает участие в рейтинге.

### `POST /api/v1/me/score`

Обновляет score текущего пользователя.

## Что хранить на mobile

Обязательно:
- `accessToken`
- `userId`

Опционально:
- `username`
- `participateInRating`

Источником истины для профиля считать `GET /api/v1/me`.
- отправлять `score` можно только если у пользователя включено участие в рейтинге

### `GET /api/v1/leaderboard/top?limit=100`

Возвращает топ пользователей только с `score >= 0`.

### `GET /api/v1/leaderboard/bottom?limit=100`

Возвращает антитоп пользователей только с `score < 0`.

Пример:

```json
{
  "items": [
    {
      "username": "player_10",
      "score": -1
    },
    {
      "username": "player_7",
      "score": -3
    }
  ],
  "total": 20
}
```

## Versioning Strategy

- `v1` — текущий стабильный public contract для mobile/web clients
- unversioned routes пока остаются как compatibility layer
- все обратно совместимые изменения можно добавлять в `v1`
- любое breaking change требует нового namespace, например `/api/v2/...`
- при появлении `v2` нужно оставлять migration window, в котором `v1` и `v2` работают параллельно

## Error Handling

Минимально на стороне мобильного приложения нужно обрабатывать:
- `200` / `201` — success
- `401` — token missing or invalid
- `409` — username already exists
- `422` — invalid data
- `429` — too many requests
- `500` — internal server error

Все ошибки API теперь приходят в одном формате:

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

## Start Here

Если начинается работа по мобильной интеграции, сначала нужно прочитать:
- `docs/HANDOFF.md`
- `README.md`
- `docs/MOBILE_API.md`

Актуальная человекочитаемая docs page для команды мобильного приложения:
- `https://api.wobbly.site/api/docs`

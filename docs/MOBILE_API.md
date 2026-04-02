# Mobile API

Этот файл описывает production public contract для мобильного клиента.

Если нужен staging contract для ручной проверки, это operational detail из `develop`, а не основная документация для production release.

## Base URL

```text
https://api.wobbly.site/api/v1
```

Legacy unversioned routes пока сохранены для обратной совместимости, но новый mobile-контракт нужно строить уже на `/api/v1/...`.

Правило:
- новые мобильные версии должны использовать только `/api/v1/...`
- legacy unversioned routes считаем временным compatibility layer

## Swagger

```text
https://api.wobbly.site/api/swagger
```

## Text Docs

```text
https://api.wobbly.site/api/docs
```

Важно:
- `/api/docs` это production text docs page
- если страница открывается пустой, сначала нужно проверить загрузку frontend assets

## Authorization

Для защищенных методов нужно передавать:

```http
Authorization: Bearer <accessToken>
```

Защищенные методы:
- `GET /api/v1/me`
- `PATCH /api/v1/me/profile`
- `PATCH /api/v1/me/rating`
- `POST /api/v1/me/score`

После включения `TrustedHostMiddleware`, ограниченного CORS и `nginx` rate limiting мобильному приложению ничего менять не нужно, если оно:
- использует `https://api.wobbly.site`
- использует versioned routes под `/api/v1/...`
- не подменяет вручную заголовок `Host`
- передает `Authorization: Bearer <accessToken>` в защищенные методы

## Storage On Mobile App Side

Нужно сохранять локально:
- `accessToken`
- `userId`

Можно дополнительно кешировать:
- `username`
- `participateInRating`

Источником истины лучше считать ответ `GET /api/v1/me`.

## Integration Flow

### First Launch

1. Проверить, есть ли локально `accessToken`
2. Если токена нет:
   - вызвать `POST /api/v1/auth/anonymous`
   - сохранить `accessToken`
   - сохранить `userId`

### Regular App Start

1. Если токен есть:
   - вызвать `GET /api/v1/me`
   - получить текущий профиль

### Profile Screen

Когда пользователь вводит имя и включает участие в рейтинге:
- вызвать `PATCH /api/v1/me/profile`

Если нужно отдельно включить или выключить себя из рейтингов:
- вызвать `PATCH /api/v1/me/rating`

### Score Update

Когда приложение хочет отправить рейтинг:
- вызвать `POST /api/v1/me/score`

### Leaderboard Screen

- `GET /api/v1/leaderboard/top?limit=100`

### Anti-Leaderboard Screen

- `GET /api/v1/leaderboard/bottom?limit=100`

## Endpoints

### `POST /api/v1/auth/anonymous`

Создает anonymous user и возвращает токен.

Request:

```json
{}
```

Response:

```json
{
  "userId": 26,
  "accessToken": "rt_xxxxx",
  "tokenType": "bearer"
}
```

### `GET /api/v1/me`

Возвращает профиль текущего авторизованного пользователя.

Response:

```json
{
  "id": 26,
  "username": null,
  "participateInRating": false
}
```

### `PATCH /api/v1/me/profile`

Обновляет имя и участие в рейтинге.

Request:

```json
{
  "username": "player_1",
  "participateInRating": true
}
```

Response:

```json
{
  "id": 26,
  "username": "player_1",
  "participateInRating": true
}
```

Правила:
- если `participateInRating = true`, `username` должен быть заполнен
- `username` должен быть уникальным
- разрешены только латинские буквы, цифры, `_`, `.`, `-`

### `PATCH /api/v1/me/rating`

Позволяет отдельно включать и выключать участие текущего пользователя в рейтинге.

Request:

```json
{
  "participateInRating": false
}
```

Response:

```json
{
  "id": 26,
  "username": "player_1",
  "participateInRating": false
}
```

Важно:
- если отправить `"participateInRating": true` без сохраненного `username`, backend вернет `422`
- если отправить `"participateInRating": false`, пользователь исключается из leaderboard

### `POST /api/v1/me/score`

Обновляет рейтинг текущего авторизованного пользователя.

Request:

```json
{
  "score": 123
}
```

Response:

```json
{
  "username": "player_1",
  "score": 123
}
```

Важно:
- мобильное приложение не должно передавать `userId`
- мобильное приложение не должно передавать `username`
- backend сам определяет пользователя по токену

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

## Chat Transfer Note

Если работа по мобильной интеграции переносится в новый чат, сначала нужно прочитать:
- `docs/HANDOFF.md`
- `README.md`
- `docs/MOBILE_API.md`

Актуальная человекочитаемая docs page для команды мобильного приложения:
- `https://api.wobbly.site/api/docs`

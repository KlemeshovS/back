# Mobile API

## Base URL

```text
https://api.wobbly.site
```

## Swagger

```text
https://api.wobbly.site/api/swagger
```

## Text Docs

```text
https://api.wobbly.site/api/docs
```

## Authorization

Для защищенных методов нужно передавать:

```http
Authorization: Bearer <access_token>
```

Защищенные методы:
- `GET /me`
- `PATCH /me/profile`
- `PATCH /me/rating`
- `POST /me/score`

## Storage On Mobile App Side

Нужно сохранять локально:
- `access_token`
- `user_id`

Можно дополнительно кешировать:
- `username`
- `participate_in_rating`

Источником истины лучше считать ответ `GET /me`.

## Integration Flow

### First Launch

1. Проверить, есть ли локально `access_token`
2. Если токена нет:
   - вызвать `POST /auth/anonymous`
   - сохранить `access_token`
   - сохранить `user_id`

### Regular App Start

1. Если токен есть:
   - вызвать `GET /me`
   - получить текущий профиль

### Profile Screen

Когда пользователь вводит имя и включает участие в рейтинге:
- вызвать `PATCH /me/profile`

Если нужно отдельно включить или выключить себя из рейтингов:
- вызвать `PATCH /me/rating`

### Score Update

Когда приложение хочет отправить рейтинг:
- вызвать `POST /me/score`

### Leaderboard Screen

- `GET /leaderboard/top?limit=100`

### Anti-Leaderboard Screen

- `GET /leaderboard/bottom?limit=100`

## Endpoints

### `POST /auth/anonymous`

Создает anonymous user и возвращает токен.

Request:

```json
{}
```

Response:

```json
{
  "user_id": 26,
  "access_token": "rt_xxxxx",
  "token_type": "bearer"
}
```

### `GET /me`

Возвращает профиль текущего авторизованного пользователя.

Response:

```json
{
  "id": 26,
  "username": null,
  "participate_in_rating": false
}
```

### `PATCH /me/profile`

Обновляет имя и участие в рейтинге.

Request:

```json
{
  "username": "player_1",
  "participate_in_rating": true
}
```

Response:

```json
{
  "id": 26,
  "username": "player_1",
  "participate_in_rating": true
}
```

Правила:
- если `participate_in_rating = true`, `username` должен быть заполнен
- `username` должен быть уникальным
- разрешены только латинские буквы, цифры, `_`, `.`, `-`

### `PATCH /me/rating`

Позволяет отдельно включать и выключать участие текущего пользователя в рейтинге.

Request:

```json
{
  "participate_in_rating": false
}
```

Response:

```json
{
  "id": 26,
  "username": "player_1",
  "participate_in_rating": false
}
```

Важно:
- если отправить `"participate_in_rating": true` без сохраненного `username`, backend вернет `422`
- если отправить `"participate_in_rating": false`, пользователь исключается из leaderboard

### `POST /me/score`

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
- мобильное приложение не должно передавать `user_id`
- мобильное приложение не должно передавать `username`
- backend сам определяет пользователя по токену

### `GET /leaderboard/top?limit=100`

Возвращает топ пользователей только с `score >= 0`.

### `GET /leaderboard/bottom?limit=100`

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

## Error Handling

Минимально на стороне мобильного приложения нужно обрабатывать:
- `200` / `201` — success
- `401` — token missing or invalid
- `409` — username already exists
- `422` — invalid data
- `429` — too many requests
- `500` — internal server error

## Legacy Endpoints

Эти методы оставлены только для обратной совместимости:
- `POST /users/register`
- `POST /users/score`

Для нового мобильного приложения использовать их не нужно.

## Chat Transfer Note

Если работа по мобильной интеграции переносится в новый чат, сначала нужно прочитать:
- `HANDOFF.md`
- `README.md`
- `MOBILE_API.md`

Актуальная человекочитаемая docs page для команды мобильного приложения:
- `https://api.wobbly.site/api/docs`

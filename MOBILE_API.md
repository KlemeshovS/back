# Mobile API

## Base URL

```text
https://api.wobbly.site
```

## Swagger

```text
https://api.wobbly.site/api/swagger
```

## Authorization

Для защищенных методов нужно передавать:

```http
Authorization: Bearer <access_token>
```

Защищенные методы:
- `GET /me`
- `PATCH /me/profile`
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

Что делать на стороне мобильного приложения:
- сохранить `user_id`
- сохранить `access_token`

### `GET /me`

Возвращает профиль текущего авторизованного пользователя.

Headers:

```http
Authorization: Bearer <access_token>
```

Response:

```json
{
  "id": 26,
  "username": null,
  "participate_in_rating": false
}
```

Пояснение:
- `username = null` означает, что имя еще не задано
- `participate_in_rating = false` означает, что пользователь пока не участвует в рейтинге

### `PATCH /me/profile`

Обновляет имя и участие в рейтинге.

Headers:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

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
- разрешены только:
  - латинские буквы
  - цифры
  - `_`
  - `.`
  - `-`

Примеры валидных имен:
- `Test`
- `test_1`
- `user.name`

Примеры невалидных имен:
- `Test!`
- `БОГ`

### `POST /me/score`

Обновляет рейтинг текущего авторизованного пользователя.

Headers:

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

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

Возвращает топ пользователей.

Response:

```json
{
  "items": [
    {
      "username": "player_1",
      "score": 2731
    },
    {
      "username": "player_2",
      "score": 1545
    }
  ],
  "total": 20
}
```

### `GET /leaderboard/bottom?limit=100`

Возвращает антитоп пользователей.

Response:

```json
{
  "items": [
    {
      "username": "player_10",
      "score": 1
    },
    {
      "username": "player_7",
      "score": 3
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

## Recommended Mobile App Scenario

### First app launch

1. Вызвать `POST /auth/anonymous`
2. Сохранить `access_token`
3. Сохранить `user_id`

### Open profile

1. Вызвать `GET /me`
2. Если `username == null`, показать форму заполнения имени

### Save profile

1. Вызвать `PATCH /me/profile`
2. Передать:

```json
{
  "username": "chosen_name",
  "participate_in_rating": true
}
```

### Send score

1. Вызвать `POST /me/score`
2. Передать:

```json
{
  "score": 123
}
```

### Open leaderboard

1. Вызвать `GET /leaderboard/top?limit=100`

### Open anti-leaderboard

1. Вызвать `GET /leaderboard/bottom?limit=100`

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

## Request Headers

### Authorization

Для защищенных методов:

```http
Authorization: Bearer <accessToken>
```

### X-Client-Platform

Опциональный заголовок для идентификации платформы клиента. Сервер сохраняет значение в сессии для аналитики.

```http
X-Client-Platform: ios
```

Допустимые значения: `ios`, `android`. Любое другое значение игнорируется.

Рекомендуется передавать во всех запросах, создающих сессию:
- `POST /api/v1/auth/anonymous`
- `POST /api/v1/auth/google`
- `POST /api/v1/auth/apple`
- `POST /api/v1/auth/yandex`

Защищенные методы:
- `GET /api/v1/me`
- `GET /api/v1/auth/session`
- `GET /api/v1/auth/providers`
- `PATCH /api/v1/me/profile`
- `PATCH /api/v1/me/rating`
- `POST /api/v1/me/avatar`
- `DELETE /api/v1/me/avatar`
- `DELETE /api/v1/me`
- `POST /api/v1/me/score`
- `POST /api/v1/auth/providers/google/link`
- `POST /api/v1/auth/providers/apple/link`
- `POST /api/v1/auth/providers/yandex/link`
- `DELETE /api/v1/auth/providers/{provider}`
- `POST /api/v1/auth/logout`

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
- `POST /api/v1/me/avatar` — загрузить аватар текущего пользователя
- `DELETE /api/v1/me/avatar` — удалить аватар текущего пользователя
- `POST /api/v1/me/score` — обновить score

### Внутренняя session model для social auth

- `GET /api/v1/auth/session` — восстановить текущую сессию по `accessToken`
- `POST /api/v1/auth/refresh` — обменять `refreshToken` на новую пару токенов
- `POST /api/v1/auth/logout` — завершить текущую сессию
- `GET /api/v1/auth/providers` — получить список привязанных способов входа
- `POST /api/v1/auth/providers/google/link` — привязать Google к текущему аккаунту
- `POST /api/v1/auth/providers/apple/link` — привязать Apple к текущему аккаунту
- `POST /api/v1/auth/providers/yandex/link` — привязать Yandex к текущему аккаунту
- `DELETE /api/v1/auth/providers/{provider}` — отвязать способ входа, если это не последний провайдер

### Таблицы рейтинга

- `GET /api/v1/leaderboard/top?limit=100`
- `GET /api/v1/leaderboard/bottom?limit=100`

## Правила backend

- участие в рейтинге можно включить только если есть `username`
- участие в рейтинге доступно только для `authenticated` session
- guest-пользователь не может сохранять `username` для рейтинга
- guest-пользователь не может включать участие в рейтинге
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
- `avatarUrl`

### `GET /api/v1/auth/session`

Возвращает текущую серверную сессию и базовое состояние пользователя.

Поля ответа:
- `userId`
- `username`
- `participateInRating`
- `sessionType` — `guest` | `authenticated`
- `provider` — `google` | `apple` | `yandex` | `null` для guest
- `avatarUrl`

### `POST /api/v1/auth/refresh`

Обновляет пару токенов по `refreshToken`.

Тело запроса:
- `refreshToken`

Поля ответа:
- `userId`
- `accessToken`
- `refreshToken`
- `tokenType`

### `POST /api/v1/auth/logout`

Завершает текущую сессию.

### `GET /api/v1/auth/providers`

Возвращает список привязанных identity providers.

Поля ответа для каждого provider:
- `provider`
- `providerEmail`
- `providerEmailVerified`
- `createdAt`
- `updatedAt`

### `POST /api/v1/auth/providers/google/link`

Привязывает Google identity к текущему authenticated account.

Тело запроса:
- `idToken`

### `POST /api/v1/auth/providers/apple/link`

Привязывает Apple identity к текущему authenticated account.

Тело запроса:
- `idToken`

### `POST /api/v1/auth/providers/yandex/link`

Привязывает Yandex identity к текущему authenticated account.

Тело запроса:
- `accessToken`

### `DELETE /api/v1/auth/providers/{provider}`

Отвязывает provider от текущего authenticated account.

Допустимые `provider`:
- `google`
- `apple`
- `yandex`

Нельзя удалить последний способ входа.

## Admin API notes

Admin UI использует отдельный admin-контур backend, но контракт managed users тоже важно держать в актуальном состоянии, потому что `/api/docs` и admin UI должны обновляться в том же изменении, что и backend API.

### `GET /admin/users`

Возвращает список управляемых пользователей для админки.

Поля ответа для каждого пользователя:
- `id`
- `username`
- `score`
- `participateInRating`
- `accountStatus`
- `identityProviders`
- `createdAt`
- `updatedAt`
- `lastSeenAt`

Где:
- `accountStatus = guest` — анонимный пользователь
- `accountStatus = active` — авторизованный/активный аккаунт
- `identityProviders` — список привязанных способов входа, например `google`, `apple`, `yandex`

### `GET /admin/users/{userId}`

Возвращает те же поля, что и список, но для одной записи пользователя в detail modal админки.

### `PATCH /api/v1/me/profile`

Сохраняет `username` и `participateInRating`.

### `PATCH /api/v1/me/rating`

Отдельно включает или выключает участие в рейтинге.

### `POST /api/v1/me/avatar`

Загружает новый аватар текущего пользователя.

Формат:
- `multipart/form-data`
- поле файла: `file`

Ограничения:
- поддерживаются `image/jpeg`, `image/png`, `image/webp`
- максимальный размер задается backend-конфигом `AVATAR_MAX_BYTES`

Ответ:
- тот же профиль, что и `GET /api/v1/me`

### `DELETE /api/v1/me/avatar`

Удаляет текущий аватар пользователя.

Ответ:
- тот же профиль, что и `GET /api/v1/me`

### `DELETE /api/v1/me`

Удаляет аккаунт текущего пользователя и все связанные данные (сессии, провайдеры, аватар).

Доступно только для `authenticated` пользователей.

Ответ: `204 No Content`

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

Дополнительно:
- в leaderboard попадают только пользователи, у которых `lastSeenAt` не старше 30 дней
- для каждого элемента может приходить `avatarUrl`

### `GET /api/v1/leaderboard/bottom?limit=100`

Возвращает антитоп пользователей только с `score < 0`.

Дополнительно:
- в leaderboard попадают только пользователи, у которых `lastSeenAt` не старше 30 дней
- для каждого элемента может приходить `avatarUrl`

Пример:

```json
{
  "items": [
    {
      "username": "player_10",
      "score": -1,
      "avatarUrl": "https://api.wobbly.site/media/avatars/user-10.jpg"
    },
    {
      "username": "player_7",
      "score": -3,
      "avatarUrl": null
    }
  ],
  "total": 20
}
```

## Friends API

Система друзей доступна только для `authenticated`-пользователей. Гость получает `403 AUTH_REQUIRED_FOR_RATING` на любом эндпоинте.

### Защищённые методы

- `POST /api/v1/friends`
- `GET /api/v1/friends`
- `GET /api/v1/friends/requests`
- `PATCH /api/v1/friends/{friendshipId}`
- `DELETE /api/v1/friends/{friendshipId}`

### Статусы дружбы

- `pending` — заявка отправлена, ждёт ответа
- `accepted` — дружба подтверждена
- `declined` — заявка отклонена

### Поля объекта дружбы (FriendResponse)

- `userId` — ID другого пользователя (не текущего)
- `username` — username другого пользователя
- `avatarUrl` — абсолютный URL аватара или `null`
- `friendshipId` — ID дружбы, используется в PATCH и DELETE
- `status` — `pending` / `accepted` / `declined`
- `isRequester` — `true`, если текущий пользователь отправил заявку
- `createdAt` — ISO 8601

### `POST /api/v1/friends`

Отправить заявку в друзья.

Тело запроса:
- `username` — username адресата

Ответ `201`: объект `FriendResponse` со статусом `pending`, `isRequester: true`.

### `GET /api/v1/friends`

Возвращает список принятых дружб (`status=accepted`).

Ответ `200`:
- `items` — массив `FriendResponse`
- `total` — общее количество

### `GET /api/v1/friends/requests`

Возвращает все pending-заявки текущего пользователя (входящие и исходящие).

Разделение:
- `isRequester: false` — входящая заявка, можно принять или отклонить
- `isRequester: true` — исходящая заявка, можно только отменить через DELETE

### `PATCH /api/v1/friends/{friendshipId}`

Принять или отклонить входящую заявку. Только адресат (`isRequester: false`).

Тело запроса:
- `action` — `accept` или `decline`

Ответ `200`: обновлённый `FriendResponse`.

### `DELETE /api/v1/friends/{friendshipId}`

Удалить друга или отменить заявку. Доступно обеим сторонам.

Ответ: `204 No Content`.

### Правила

- Лимит — 200 принятых дружб на пользователя
- Нельзя отправить заявку самому себе
- Нельзя отправить повторную заявку, пока существует pending/accepted/declined запись
- Только `authenticated`-пользователи

### Коды ошибок Friends

- `AUTH_REQUIRED_FOR_RATING` — гость пытается работать с друзьями
- `USER_NOT_FOUND` — username не существует или аккаунт неактивен
- `CANNOT_ADD_SELF` — попытка добавить себя в друзья
- `ALREADY_FRIENDS` — пользователи уже являются друзьями
- `FRIEND_REQUEST_ALREADY_SENT` — заявка в любую сторону уже существует
- `FRIENDS_LIMIT_REACHED` — достигнут лимит 200 принятых дружб
- `FRIEND_REQUEST_NOT_FOUND` — заявка не найдена или не принадлежит текущему пользователю
- `NOT_FRIENDS` — дружба не найдена (DELETE)

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
- `AUTH_REQUIRED_FOR_RATING` — требуется авторизация для участия в рейтинговом контуре, например для отправки `score`
- `AUTH_REQUIRED_FOR_USERNAME` — требуется авторизация для сохранения `username`
- `GUEST_CANNOT_ENABLE_RATING` — guest-пользователь пытается включить участие в рейтинге

Временный режим совместимости:
- если на backend включен `ALLOW_GUEST_RATING=true`, guest-пользователи временно могут сохранять `username`, включать участие в рейтинге и отправлять `score`
- по умолчанию этот режим выключен
- `AUTH_REQUIRED_FOR_PROVIDER_MANAGEMENT` — guest-пользователь пытается управлять привязанными способами входа
- `MISSING_AUTHORIZATION_HEADER` — в запросе отсутствует заголовок `Authorization: Bearer <accessToken>`
- `INVALID_AUTHORIZATION_HEADER` — заголовок `Authorization` передан в неправильном формате
- `INVALID_TOKEN` — токен передан, но не найден в системе или больше невалиден
- `IDENTITY_ALREADY_LINKED` — этот social account уже привязан к другому internal user
- `PROVIDER_ALREADY_LINKED` — этот provider уже привязан к текущему аккаунту с другим external id
- `PROVIDER_NOT_LINKED` — у текущего аккаунта нет такого привязанного provider
- `LAST_IDENTITY_REQUIRED` — нельзя отвязать последний способ входа
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

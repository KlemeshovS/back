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
- в leaderboard попадают только пользователи, у которых `updatedAt` не старше 30 дней
- для каждого элемента может приходить `avatarUrl`

### `GET /api/v1/leaderboard/bottom?limit=100`

Возвращает антитоп пользователей только с `score < 0`.

Дополнительно:
- в leaderboard попадают только пользователи, у которых `updatedAt` не старше 30 дней
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

## Follows API (подписки и друзья)

Система подписок доступна только для `authenticated`-пользователей. Гость получает `403 AUTH_REQUIRED_FOR_RATING`.

Модель: **подписка односторонняя**. Взаимная подписка автоматически означает дружбу — никаких заявок, статусов и подтверждений нет.

### Защищённые методы

- `POST /api/v1/follows`
- `DELETE /api/v1/follows/{userId}`
- `GET /api/v1/follows`
- `GET /api/v1/follows/followers`
- `GET /api/v1/follows/friends`

### Поля объекта подписки (FollowResponse)

- `userId` — ID другого пользователя
- `username` — username другого пользователя
- `avatarUrl` — абсолютный URL аватара или `null`
- `isMutual` — `true`, если подписка взаимная (= друзья)
- `createdAt` — ISO 8601

### `POST /api/v1/follows`

Подписаться на пользователя по username.

Тело запроса:
- `username` — username цели

Ответ `201`: `FollowResponse`. Если другой уже подписан на вас — `isMutual: true`.

### `DELETE /api/v1/follows/{userId}`

Отписаться от пользователя. `userId` — ID пользователя, от которого отписываемся.

Ответ: `204 No Content`.

### `GET /api/v1/follows`

Список пользователей, на которых подписан текущий пользователь (мои подписки).

Ответ `200`:
- `items` — массив `FollowResponse`
- `total` — общее количество

### `GET /api/v1/follows/followers`

Список пользователей, которые подписаны на текущего пользователя (мои подписчики).

### `GET /api/v1/follows/friends`

Список пользователей с взаимной подпиской (друзья). Все элементы имеют `isMutual: true`.

### Правила

- Лимит подписок — 500 на пользователя
- Нельзя подписаться на себя
- Только `authenticated`-пользователи
- Дружба = взаимная подписка, отдельного подтверждения не требует

### Коды ошибок Follows

- `AUTH_REQUIRED_FOR_RATING` — гость пытается работать с подписками
- `USER_NOT_FOUND` — username не существует или аккаунт неактивен
- `CANNOT_FOLLOW_SELF` — попытка подписаться на себя
- `ALREADY_FOLLOWING` — уже подписан на этого пользователя
- `FOLLOWS_LIMIT_REACHED` — достигнут лимит 500 подписок
- `NOT_FOLLOWING` — попытка отписаться от пользователя, на которого не подписан

## Calendar API (ежедневные записи)

Хранит ежедневные записи пользователя (уровень употребления алкоголя и спорта). Доступно для всех пользователей (в том числе гостей).

### Защищённые методы

- `PUT /api/v1/me/calendar`
- `GET /api/v1/me/calendar`

### Формат дат и значений

Ключ — дата в формате `YYYY-M-D` (без leading zero). Значение — целое число (`DrinkLevel`):

| Значение | Смысл           |
|----------|-----------------|
| `0`      | трезвый         |
| `1`      | мало            |
| `2`      | средне          |
| `3`      | много           |
| `4`      | спорт           |
| `5`      | мало + спорт    |
| `6`      | средне + спорт  |
| `7`      | много + спорт   |

### `PUT /api/v1/me/calendar`

Полностью заменяет текущий календарь пользователя. Отправляется весь словарь целиком.

Тело запроса:

```json
{
  "days": {
    "2024-1-15": 0,
    "2024-1-16": 4,
    "2024-1-17": 1
  },
  "clientUpdatedAt": "2024-01-15T11:00:00Z"
}
```

`clientUpdatedAt` — опциональное поле. Если передано, сервер проверяет, не изменил ли другой девайс данные позже. Если сервер новее — возвращает `409 CALENDAR_CONFLICT`.

Ответ `200`:

```json
{
  "days": {
    "2024-1-15": 0,
    "2024-1-16": 4,
    "2024-1-17": 1
  },
  "updatedAt": "2024-01-15T12:00:00Z"
}
```

### `GET /api/v1/me/calendar`

Возвращает текущий сохранённый календарь. Если данных ещё нет — возвращает пустой словарь и `updatedAt = "1970-01-01T00:00:00Z"` (эпоха) — сигнал, что сервер пустой и клиент всегда выигрывает сравнение.

Ответ `200`:

```json
{
  "days": {},
  "updatedAt": "1970-01-01T00:00:00Z"
}
```

### Офлайн-синхронизация

Клиент хранит локально `days` + `localUpdatedAt` (время последнего изменения на устройстве).

**При выходе в онлайн:**

1. `GET /api/v1/me/calendar` → получить `{days, updatedAt}` с сервера
2. Если `localUpdatedAt > updatedAt` → отправить локальные данные через `PUT` с `clientUpdatedAt = localUpdatedAt`
3. Если `updatedAt > localUpdatedAt` → обновить локальные данные из ответа сервера
4. Если равны → ничего не делать

**Защита от перезаписи при мультидевайсе:**

Если `PUT` возвращает `409 CALENDAR_CONFLICT` — другой девайс сохранил данные позже, чем `clientUpdatedAt`. Нужно сделать повторный `GET`, смёржить данные на клиенте и снова отправить `PUT`.

### Правила

- Максимальный размер payload — 512 KB
- Ключи не валидируются на стороне backend — валидация на стороне клиента
- Словарь заменяется целиком при каждом `PUT`
- `updatedAt` — время последнего `PUT` на сервере (ISO 8601, UTC)

### Коды ошибок Calendar

- `CALENDAR_TOO_LARGE` (`413`) — размер сохраняемых данных превышает 512 KB
- `CALENDAR_CONFLICT` (`409`) — другой девайс сохранил данные позже, чем `clientUpdatedAt`; нужно смёржить локально и повторить `PUT`
- `USER_NOT_FOUND` (`404`) — пользователь не найден (не должно возникать при нормальной авторизации)
- `INTERNAL_SERVER_ERROR` (`500`) — непредвиденная ошибка сервера

## Triggers API (дневник триггеров)

Хранит причины употребления алкоголя по дням (дневник триггеров) — **строго приватные данные**, никогда не отдаются другим пользователям (нет аналога `GET /users/{userId}/calendar/triggers`).

### Защищённые методы

- `PUT /api/v1/me/calendar/triggers`
- `GET /api/v1/me/calendar/triggers`

### Формат дат и значений

Ключ — дата в формате `YYYY-M-D` (тот же формат, что у Calendar). Значение — список тегов из фиксированного набора:

| Тег         | Смысл                          |
|-------------|---------------------------------|
| `stress`    | стресс                          |
| `boredom`   | скука                            |
| `party`     | тусовка/праздник                 |
| `company`   | уговорили                        |
| `loneliness`| одиночество                      |
| `conflict`  | конфликт                         |
| `habit`     | привычка                         |
| `other`     | другое                           |

На один день может приходиться несколько тегов сразу.

### `PUT /api/v1/me/calendar/triggers`

Полностью заменяет сохранённый дневник триггеров. Отправляется весь словарь целиком.

Тело запроса:

```json
{
  "triggers": {
    "2024-1-15": ["stress", "conflict"],
    "2024-1-16": ["habit"]
  },
  "clientUpdatedAt": "2024-01-15T11:00:00Z"
}
```

`clientUpdatedAt` — опциональное поле, та же логика конфликта, что у Calendar: если сервер новее — `409 TRIGGERS_CONFLICT`.

Любое значение тега вне списка выше отклоняется как `422 Unprocessable Entity` ещё на этапе валидации запроса.

Ответ `200`:

```json
{
  "triggers": {
    "2024-1-15": ["stress", "conflict"],
    "2024-1-16": ["habit"]
  },
  "updatedAt": "2024-01-15T12:00:00Z"
}
```

### `GET /api/v1/me/calendar/triggers`

Возвращает текущий сохранённый дневник триггеров. Если данных ещё нет — пустой словарь и `updatedAt = "1970-01-01T00:00:00Z"` (эпоха), как и у Calendar.

### Правила

- Максимальный размер payload — 512 KB
- Значения тегов валидируются на стороне backend (allowlist из 8 значений выше)
- Словарь заменяется целиком при каждом `PUT`
- Данные никогда не включаются в friend-calendar ответы

### Коды ошибок Triggers

- `TRIGGERS_TOO_LARGE` (`413`) — размер сохраняемых данных превышает 512 KB
- `TRIGGERS_CONFLICT` (`409`) — другой девайс сохранил данные позже, чем `clientUpdatedAt`; нужно смёржить локально и повторить `PUT`
- `USER_NOT_FOUND` (`404`) — пользователь не найден (не должно возникать при нормальной авторизации)
- `INTERNAL_SERVER_ERROR` (`500`) — непредвиденная ошибка сервера

## Bets API (пари между взаимными друзьями)

Пари — вызов, который пользователь бросает взаимному другу на одно из четырёх событий. Ставки не денежные. Победитель определяется **сервером**, на основе уже синкающихся календарных данных обоих участников (`calendar_data`), а не на основании того, что пришлёт клиент — это исключает читерство.

### Защищённые методы

- `POST /api/v1/me/bets` — бросить вызов
- `GET /api/v1/me/bets` — все пари пользователя (входящие/активные/история)
- `GET /api/v1/me/bets/{betId}` — детали одного пари
- `POST /api/v1/me/bets/{betId}/accept` — принять
- `POST /api/v1/me/bets/{betId}/decline` — отклонить
- `POST /api/v1/me/bets/{betId}/cancel` — отозвать (только автор, только pending)
- `POST /api/v1/me/bets/{betId}/forfeit` — слиться (только active)

### Типы пари (`betType`)

| Тип          | Механика                                                                 |
|--------------|---------------------------------------------------------------------------|
| `sobriety`   | На вылет: первый алкогольный день в окне пари — проигрыш. Ничья, если оба сорвались в один день или оба продержались весь срок. |
| `sport`      | У кого больше дней со спортом за весь срок.                              |
| `score_up`   | У кого больше очков за срок (считаются с нуля от старта пари).           |
| `score_down` | Та же метрика, что и `score_up`, но побеждает тот, у кого очков меньше.  |

Равенство значений в `sport`/`score_up`/`score_down` — ничья (`winnerId = null`).

### Срок (`durationMode`)

- `period` — количество дней (`durationDays`, 1–366). Пари стартует **не сразу, а с момента принятия** оппонентом. Дедлайн на принятие равен тому же сроку: если вызов не приняли в течение `durationDays` дней с момента создания — он считается просроченным (`expired`).
- `fixed_date` — конкретная дата (`targetEndDate`, `YYYY-MM-DD`, должна быть в будущем на момент создания). Дедлайн на принятие = конец этой даты; после неё непринятый вызов тоже считается `expired`.

### `POST /api/v1/me/bets`

```json
{
  "opponentUserId": 42,
  "betType": "sobriety",
  "durationMode": "period",
  "durationDays": 14
}
```

или

```json
{
  "opponentUserId": 42,
  "betType": "score_up",
  "durationMode": "fixed_date",
  "targetEndDate": "2026-12-31"
}
```

Оппонент должен быть взаимным другом (`403 BET_NOT_MUTUAL_FRIEND`), нельзя бросить вызов себе (`422 BET_CANNOT_CHALLENGE_SELF`).

Ответ `201` — объект пари в статусе `pending`:

```json
{
  "id": 17,
  "challenger": {"userId": 1, "username": "vasya", "avatarUrl": null},
  "opponent": {"userId": 42, "username": "petya", "avatarUrl": null},
  "betType": "sobriety",
  "durationMode": "period",
  "durationDays": 14,
  "targetEndDate": null,
  "status": "pending",
  "resolutionType": null,
  "winnerId": null,
  "forfeitedBy": null,
  "respondBy": "2026-09-01T12:00:00Z",
  "startAt": null,
  "endAt": null,
  "resultSnapshot": null,
  "liveSnapshot": null,
  "createdAt": "2026-08-18T12:00:00Z",
  "acceptedAt": null,
  "resolvedAt": null
}
```

### Жизненный цикл (`status` / `resolutionType`)

```
pending ──accept──▶ active ──(время истекло / срыв)──▶ resolved (resolutionType=natural)
   │                    │
   │ decline            │ forfeit
   ▼                    ▼
resolved             resolved (resolutionType=forfeit, forfeitedBy=тот кто слился)
(resolutionType=declined)

   │ cancel (только автор, пока pending)
   ▼
resolved (resolutionType=cancelled)

   │ дедлайн принятия истёк
   ▼
resolved (resolutionType=expired)
```

`status` — всего три значения: `pending`, `active`, `resolved`. Детали исхода — в `resolutionType` (`declined` / `cancelled` / `expired` / `forfeit` / `natural`) и `winnerId` (`null` = ничья, либо исход без победителя — declined/cancelled/expired).

**Важно:** резолюция `pending`→`expired` и `active`→`resolved` (по истечении срока или по срыву в `sobriety`-пари) происходит **лениво** — при любом чтении (`GET /me/bets` или `GET /me/bets/{id}`) сервер сначала проверяет, не истёк ли дедлайн/срок, и если да — пересчитывает и сохраняет исход перед тем как вернуть ответ. Отдельного cron/scheduler нет.

`resultSnapshot` — финальные цифры на момент завершения (например `{"challengerValue": 3, "opponentValue": 1}` для `sport`), нужен для отображения в Истории без повторного запроса календаря.

`liveSnapshot` — те же цифры, но текущие (не персистятся, считаются на каждый `GET` заново) для ещё **активного** пари типа `sport`/`score_up`/`score_down`, чтобы показать текущий счёт до того, как пари завершится. Для `sobriety` всегда `null` (пока пари активно, оба участника по определению ещё не сорвались — показывать нечего), для `pending`/`resolved` тоже всегда `null` (в `resolved` цифры уже в `resultSnapshot`).

### `GET /api/v1/me/bets`

Возвращает **все** пари пользователя (где он challenger или opponent), новые сверху. Разбивку на входящие вызовы / активные / историю делает клиент по полям `status` + `opponent.userId == me` (входящий вызов — это `status=pending` и я `opponent`).

### `POST /api/v1/me/bets/{betId}/accept`

Только `opponent`, только пока `status=pending`. Запускает отсчёт срока с этого момента (`startAt = now`, `endAt` вычисляется по `durationDays`/`targetEndDate`). Иначе `409 BET_INVALID_STATE`.

### `POST /api/v1/me/bets/{betId}/decline` и `.../cancel`

`decline` — только `opponent`, `cancel` — только `challenger`, оба только пока `status=pending`.

### `POST /api/v1/me/bets/{betId}/forfeit`

Любой участник, только пока `status=active`. Автоматическая победа второго участника (`resolutionType=forfeit`, `forfeitedBy` = тот, кто слился).

### Коды ошибок Bets

- `BET_NOT_FOUND` (`404`)
- `BET_CANNOT_CHALLENGE_SELF` (`422`)
- `BET_NOT_MUTUAL_FRIEND` (`403`) — оппонент не взаимный друг
- `BET_FORBIDDEN` (`403`) — действие доступно другой роли (например, отклонить может только оппонент)
- `BET_INVALID_STATE` (`409`) — действие не подходит текущему статусу пари (например, принять уже принятое)

## Calendar друга

### `GET /api/v1/users/{userId}/calendar`

Возвращает календарь другого пользователя. Доступно только если между текущим пользователем и целевым есть **взаимная подписка** (оба подписаны друг на друга).

Ответ `200` — тот же формат что и `GET /me/calendar`:

```json
{
  "days": {
    "2024-1-15": 0,
    "2024-1-16": 4
  },
  "updatedAt": "2024-01-15T12:00:00Z"
}
```

### Коды ошибок

- `NOT_FRIENDS` (`403`) — нет взаимной подписки
- `USER_NOT_FOUND` (`404`) — пользователь не найден

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

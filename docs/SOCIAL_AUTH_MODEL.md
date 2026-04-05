# Social-Only Auth Model

Технический дизайн для новой авторизации в backend.

Цель:

- не ломать текущий guest flow приложения
- требовать авторизацию только для участия в рейтингах
- перейти от `anonymous token = пользователь` к модели постоянного аккаунта
- поддержать только social-only провайдеры:
  - Google
  - Apple (`iOS`)
  - Yandex

## Текущее состояние

Сейчас backend хранит пользователей в таблице `users` и ищет текущего пользователя по:

- `users.auth_token_hash`

Anonymous auth создает полноценную запись в `users`, а bearer token фактически является единственным идентификатором аккаунта.

Проблемы текущей модели:

- потеря token = потеря identity
- невозможно безопасно восстанавливать пользователя
- guest и permanent account не разделены
- нельзя бесшовно добавить social login без новой модели identity

## Целевая модель

Нужно разделить три сущности:

1. internal user
2. external identity provider
3. session

И отдельно оставить временный guest context для неавторизованного использования приложения.

## 1. Internal user

`internal user` — это постоянный серверный аккаунт.

Он является источником истины для:

- `username`
- `score`
- `participateInRating`
- server-side profile state
- audit / ownership

### Предлагаемая модель

Таблица: `users`

Поля:

- `id`
- `username`
- `is_rating_enabled`
- `score`
- `created_at`
- `updated_at`
- `last_seen_at`
- `guest_migration_key` — временный ключ для привязки legacy guest state, nullable
- `status` — `guest` / `active`, либо bool-флаг `is_guest`

### Принцип

- permanent user живет независимо от конкретного access token
- score и username принадлежат user, а не token
- social provider никогда не является самим пользователем

## 2. External identities

Нужна отдельная таблица для привязки внешних провайдеров к internal user.

Таблица: `user_identities`

Поля:

- `id`
- `user_id` -> `users.id`
- `provider` — enum:
  - `google`
  - `apple`
  - `yandex`
- `provider_user_id` — стабильный id пользователя у провайдера
- `provider_email` — nullable
- `provider_email_verified` — bool
- `provider_payload` — jsonb, только для безопасного минимального набора полей
- `created_at`
- `updated_at`

### Ограничения

- уникальность по `(provider, provider_user_id)`
- у одного internal user может быть несколько identities
- одна external identity может принадлежать только одному internal user

### Принцип

- Google / Apple / Yandex — это только способы входа
- internal user может иметь:
  - только Google
  - только Apple
  - только Yandex
  - несколько привязанных провайдеров одновременно

## 3. Sessions

Нужна отдельная session model.

Таблица: `user_sessions`

Поля:

- `id`
- `user_id` -> `users.id`
- `access_token_hash`
- `refresh_token_hash` — nullable, если решим поддерживать refresh
- `session_type`:
  - `guest`
  - `authenticated`
- `provider` — nullable, для информации о том, каким способом был создан session
- `device_id` — nullable
- `client_platform` — nullable
- `created_at`
- `expires_at`
- `last_seen_at`
- `revoked_at` — nullable

### Принцип

- token больше не хранится в `users`
- token хранится в `user_sessions`
- access token — opaque bearer token, который backend хранит только в виде hash
- refresh token — отдельный opaque bearer token, который backend хранит только в виде hash
- access token используется для обычных API вызовов и `GET /auth/session`
- refresh token используется только для `POST /auth/refresh`
- `POST /auth/logout` отзывает текущую session

## 4. Guest state

Guest mode должен остаться, но больше не должен считаться полноценным permanent account.

### Что такое guest

Guest — это пользователь без авторизации, который:

- может пользоваться приложением
- может смотреть рейтинги
- не может участвовать в рейтинге
- не может закрепить рейтинг-identity без social login

### Где хранится guest

Есть два допустимых этапа:

#### Этап миграции

Временно поддерживаем legacy guest-пользователя в `users`:

- `users.status = 'guest'`
- или `users.is_guest = true`

Это нужно только для безопасного перехода существующих пользователей.

#### Целевая модель

После migration window:

- guest state либо живет локально на клиенте
- либо серверно хранится как временная session/state запись, но не как полноценный permanent account

## 5. Связь guest state и permanent account

Нужно поддержать бесшовную миграцию существующего guest в authenticated account.

### Предлагаемый flow

1. У пользователя уже есть legacy guest token.
2. Пользователь проходит Google / Apple / Yandex login.
3. Backend валидирует provider result.
4. Backend находит или создает permanent internal user.
5. Backend связывает legacy guest state с permanent user.
6. Backend переносит данные.
7. Backend создает authenticated session.

### Что переносим

Если у guest уже есть данные, переносим:

- `username`
- `score`
- `is_rating_enabled`
- `last_seen_at`

### Правило при конфликте

Если permanent user уже существует и у него уже есть свои данные:

- `score` не теряем и не затираем молча
- `username` не затираем молча
- нужен предсказуемый merge policy

Базовое правило:

- если authenticated account новый и пустой — переносим все guest данные
- если authenticated account уже существует:
  - `username`: приоритет у existing permanent account
  - `is_rating_enabled`: приоритет у explicit permanent account state
  - `score`: брать максимум по `updated_at`, либо явно серверное текущее значение permanent account

Для MVP безопаснее так:

- миграция разрешена только если target account еще не имеет своего рейтингового профиля
- иначе возвращаем controlled conflict и просим отдельный merge flow позже

## 6. Правила участия в рейтинге

Участие в рейтинге разрешено только если:

- пользователь авторизован
- у пользователя есть публичный `username`
- `is_rating_enabled = true`

Если пользователь:

- guest — может только смотреть
- authenticated без `username` — может пользоваться приложением, но не участвовать
- authenticated с `username`, но с выключенным флагом — может смотреть, но не участвует

`score`:

- всегда хранится на user account
- не удаляется при выключении участия
- не удаляется при смене username

## 7. Google / Apple / Yandex identities

### Google

Хранить:

- `provider = 'google'`
- `provider_user_id = sub`
- `provider_email`
- `provider_email_verified`

### Apple

Хранить:

- `provider = 'apple'`
- `provider_user_id = sub`
- `provider_email` — nullable / relay email
- `provider_email_verified`

Важно:

- Apple email может быть скрытым и нестабильным как главный ключ
- главным ключом должен быть именно `sub`

### Yandex

Хранить:

- `provider = 'yandex'`
- `provider_user_id`
- `provider_email`
- `provider_email_verified`, если доступно

### Общий принцип

- никогда не линковать аккаунт только по email без проверки provider id
- главным stable identity ключом является `(provider, provider_user_id)`

## 8. Session / refresh tokens

### MVP

Можно начать так:

- выдавать новый internal access token
- хранить его hash в `user_sessions`
- refresh token можно добавить сразу или вторым этапом

### Рекомендуемая модель

- short-lived access token
- long-lived refresh token
- revoke session при logout
- поддерживать несколько активных sessions на одного user

## 9. Правила миграции legacy guest-пользователей

### Нужно сохранить

- существующие guest users не должны внезапно “обнулиться”
- существующие username и score не должны теряться при social login

### Migration rules

1. Пока migration не завершен, legacy `/auth/anonymous` остается.
2. Legacy guest users продолжают работать.
3. При первой попытке участвовать в рейтингах показываем social auth.
4. После успешного login backend пытается выполнить `guest -> authenticated migration`.
5. После успешной миграции:
   - legacy guest session revoke
   - создается authenticated session
   - user дальше живет как permanent account

### Когда legacy anonymous можно выключать

Только после того, как:

- mobile переведен на новый flow
- migration path оттестирован
- доля активных legacy guest-пользователей стала приемлемо низкой

## 10. Этапы внедрения

### Этап 1

- добавить session model
- добавить external identities
- не ломать legacy anonymous

### Этап 2

- добавить Google / Apple / Yandex auth endpoints
- добавить internal authenticated sessions

### Этап 3

- добавить `guest -> authenticated migration`
- mobile начинает вызывать migration flow

### Этап 4

- участие в рейтинге только для authenticated users
- guest остается только view-only

### Этап 5

- постепенный уход от legacy anonymous как permanent server identity

## 11. Что не делаем в этой задаче

Эта задача только про проектирование модели.

Не входит:

- реализация OAuth endpoints
- реализация mobile UI
- финальный merge policy для сложных account conflicts
- полное удаление legacy anonymous flow

## 12. Рекомендуемые следующие задачи

1. Добавить таблицы `user_identities` и `user_sessions`
2. Убрать token storage из `users` в сторону session model
3. Спроектировать и реализовать endpoint guest migration
4. Реализовать Google auth
5. Реализовать Apple auth
6. Реализовать Yandex auth
7. Ограничить участие в рейтинге только authenticated users

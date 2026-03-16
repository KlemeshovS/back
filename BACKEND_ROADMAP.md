# Backend Roadmap

## Current State

Сейчас backend уже умеет:
- создавать anonymous user и выдавать bearer token
- регистрировать уникальный `username`
- возвращать `id` пользователя при регистрации
- обновлять `score` по `username`
- обновлять `score` по `user_id`
- обновлять `score` от авторизованного пользователя через `/me/score`
- отдельно включать и выключать участие через `/me/rating`
- отдавать `top 100` и `bottom 100`
- работать на `https://api.wobbly.site`
- ограничивать частоту регистрации и обновления рейтинга через rate limiting

Дополнительно уже сделано:
- проект разнесен на `app/api`, `app/services`, `app/core`, `app/db`, `app/domain`
- добавлены `ruff` и `pytest`
- добавлены unit tests и integration tests
- CI/CD уже автоматизирован через GitHub Actions

Это нормальный MVP, но для реального production ему не хватает защиты, наблюдаемости и более строгой модели данных.

## Priority 1: Security

### 1. ~~Add client authentication~~

Status:
- done
- добавлен `POST /auth/anonymous`
- backend выдает bearer token
- появились защищенные endpoint'ы `/me`, `/me/profile`, `/me/rating`, `/me/score`

### 2. ~~Limit abuse and spam~~

Status:
- done
- rate limiting уже добавлен для регистрации по IP
- rate limiting уже добавлен для обновления рейтинга
- осталось отдельно реализовать логирование подозрительных всплесков запросов

### 3. Harden input validation

Что сделать:
- определить допустимый диапазон `score`
- решить, можно ли уменьшать `score`, или только обновлять на новое значение
- при необходимости усилить правила `username`

## Priority 2: Data Model

### 4. Split current state and history

Сейчас хранится только текущее значение `score`.

Что сделать:
- оставить таблицу `users` для актуального состояния
- добавить таблицу `score_events`
- писать туда историю изменений: `old_score`, `new_score`, `source`, `created_at`

### 5. Add timestamps and audit fields

Что сделать:
- хранить `created_at`, `updated_at`, `last_seen_at`
- при обновлении рейтинга обновлять `last_seen_at`

### 6. Add migration tool

Что сделать:
- подключить `Alembic`
- хранить изменения схемы как миграции

## Priority 3: Reliability

### 7. Add automated backups

Что сделать:
- ежедневный `pg_dump`
- хранить несколько последних копий
- выносить бэкапы за пределы сервера, например в S3-compatible storage

### 8. ~~Improve deployment flow~~

Status:
- done
- есть `DEPLOY.md`
- есть GitHub Actions pipeline
- после merge в `main` идет автоматический verify + deploy
- ручной deploy оставлен как fallback

### 9. Add health checks and readiness checks

Что сделать:
- оставить `/health`
- добавить `/ready`, который проверяет доступность PostgreSQL

## Priority 4: Observability

### 10. Add structured logging

Что сделать:
- перейти на JSON-логи
- писать `request_id`, endpoint, status code, latency

### 11. Add error monitoring

Что сделать:
- подключить Sentry или аналог
- отправлять unhandled exceptions и важные warnings

### 12. Add metrics

Что сделать:
- собирать количество запросов
- ошибки по endpoint
- время ответа
- количество обновлений рейтинга

## Priority 5: API Evolution

### 13. Version the API

Что сделать:
- перевести маршруты на `/api/v1/...`

### 14. Improve response contract

Status:
- in progress
- регистрация уже возвращает `id` и `username`
- обновление рейтинга уже поддерживает `user_id`
- осталось унифицировать ошибки в формате `code` + `message`

Что сделать:
- унифицировать ошибки
- возвращать коды и понятные поля, например `code`, `message`

### 15. Add pagination and richer leaderboard queries

Что сделать:
- кроме `limit`, добавить `offset`
- сделать выдачу позиции конкретного пользователя
- добавить фильтры, если появятся режимы рейтингов

## Priority 6: Testing

### 16. Add automated tests

Status:
- in progress
- добавлены unit tests для auth, rate limiter и schema validation
- добавлены integration tests для API endpoint'ов
- тесты и lint checks подключены в CI
- дальше нужны integration tests со сценариями на тестовой БД

Что сделать:
- ~~unit tests для валидации~~
- ~~integration tests для API~~
- тесты на ошибки: duplicate username, missing user, invalid payload
- тесты с реальной тестовой PostgreSQL или изолированной test DB

### 17. Add staging checks

Что сделать:
- перед деплоем гонять тесты и basic smoke checks

## Suggested Execution Order

### Phase 1
- unified error responses
- тесты на ошибочные сценарии

### Phase 2
- Alembic migrations
- score history table
- backups
- readiness endpoint

### Phase 3
- structured logging
- Sentry
- metrics

### Phase 4
- API versioning
- richer leaderboard methods
- anti-fraud rules

## Recommended First Task

Если выбирать одно следующее улучшение, лучше всего сделать:

`Unify error responses for mobile client`

Следующий полезный шаг — привести ошибки к единому контракту `code` + `message`.

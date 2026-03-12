# Backend Roadmap

## Current State

Сейчас backend уже умеет:
- регистрировать уникальный `username`
- возвращать `id` пользователя при регистрации
- обновлять `score` по `username`
- обновлять `score` по `user_id`
- отдавать `top 100` и `bottom 100`
- работать на `https://api.wobbly.site`
- ограничивать частоту регистрации и обновления рейтинга через rate limiting

Это нормальный MVP, но для реального production ему не хватает защиты, наблюдаемости и более строгой модели данных.

## Priority 1: Security

### 1. Add client authentication

Сейчас любой внешний клиент может отправить любой `username` и любой `score`.

Что сделать:
- добавить `X-API-Key` или `Authorization` token для запросов от мобильного приложения
- хранить секрет в переменных окружения
- отклонять запросы без валидного ключа

Результат:
- случайные внешние запросы перестанут писать данные в вашу БД

### 2. ~~Limit abuse and spam~~

Status:
- done
- rate limiting уже добавлен для регистрации по IP
- rate limiting уже добавлен для обновления рейтинга по IP и по `username`
- осталось отдельно реализовать логирование подозрительных всплесков запросов

Что сделать:
- ~~добавить rate limiting по IP и по `username`~~
- ~~ограничить частоту обновления рейтинга~~
- логировать подозрительные всплески запросов

Результат:
- меньше риска накрутки и перегрузки API

### 3. Harden input validation

Что сделать:
- запретить нежелательные `username`
- определить допустимый диапазон `score`
- решить, можно ли уменьшать `score`, или только обновлять на новое значение

Результат:
- меньше мусорных и сломанных данных в таблице

## Priority 2: Data Model

### 4. Split current state and history

Сейчас хранится только текущее значение `score`.

Что сделать:
- оставить таблицу `users` для актуального состояния
- добавить таблицу `score_events`
- писать туда историю изменений: `username`, `old_score`, `new_score`, `source`, `created_at`

Результат:
- можно расследовать ошибки и накрутку
- можно строить аналитику и графики

### 5. Add timestamps and audit fields

Что сделать:
- хранить `created_at`, `updated_at`, `last_seen_at`
- при обновлении рейтинга обновлять `last_seen_at`

Результат:
- видно активность пользователей
- проще чистить неактуальные данные

### 6. Add migration tool

Что сделать:
- подключить `Alembic`
- хранить изменения схемы как миграции

Результат:
- безопасные изменения БД без ручного SQL

## Priority 3: Reliability

### 7. Add automated backups

Что сделать:
- ежедневный `pg_dump`
- хранить несколько последних копий
- выносить бэкапы за пределы сервера, например в S3-compatible storage

Результат:
- БД можно восстановить после ошибки или падения сервера

### 8. Improve deployment flow

Что сделать:
- завести отдельный `DEPLOY.md`
- автоматизировать деплой через GitHub Actions или простой deploy script
- сделать systemd reload/restart частью стандартного процесса

Результат:
- меньше ручных ошибок при выкладке

### 9. Add health checks and readiness checks

Что сделать:
- оставить `/health`
- добавить `/ready`, который проверяет доступность PostgreSQL

Результат:
- проще мониторить, живо ли приложение на самом деле

## Priority 4: Observability

### 10. Add structured logging

Что сделать:
- перейти на JSON-логи
- писать `request_id`, endpoint, status code, latency

Результат:
- проще искать проблемы и анализировать запросы

### 11. Add error monitoring

Что сделать:
- подключить Sentry или аналог
- отправлять unhandled exceptions и важные warnings

Результат:
- ошибки будут видны сразу, а не только по жалобам пользователей

### 12. Add metrics

Что сделать:
- собирать количество запросов
- ошибки по endpoint
- время ответа
- количество обновлений рейтинга

Результат:
- можно понимать нагрузку и деградации

## Priority 5: API Evolution

### 13. Version the API

Что сделать:
- перевести маршруты на `/api/v1/...`

Результат:
- можно спокойно развивать API без поломки мобильного клиента

### 14. Improve response contract

Status:
- in progress
- регистрация уже возвращает `id` и `username`
- обновление рейтинга уже поддерживает `user_id`
- осталось унифицировать ошибки в формате `code` + `message`

Что сделать:
- унифицировать ошибки
- возвращать коды и понятные поля, например `code`, `message`

Результат:
- Flutter-клиент проще поддерживать

### 15. Add pagination and richer leaderboard queries

Что сделать:
- кроме `limit`, добавить `offset`
- сделать выдачу позиции конкретного пользователя
- добавить фильтры, если появятся режимы рейтингов

Результат:
- API будет готово к росту функциональности

## Priority 6: Testing

### 16. Add automated tests

Что сделать:
- unit tests для валидации
- integration tests для API
- тесты на ошибки: duplicate username, missing user, invalid payload

Результат:
- меньше регрессий при доработках

### 17. Add staging checks

Что сделать:
- перед деплоем гонять тесты и basic smoke checks

Результат:
- меньше шансов сломать production

## Suggested Execution Order

### Phase 1
- auth token for client requests
- unified error responses
- tests for current endpoints

### Phase 2
- Alembic migrations
- score history table
- backups
- readiness endpoint

### Phase 3
- structured logging
- Sentry
- metrics
- deployment automation

### Phase 4
- API versioning
- richer leaderboard methods
- anti-fraud rules

## Recommended First Task

Если выбирать одно следующее улучшение, то лучше всего сделать:

`Add API authentication between Flutter app and backend`

Это самое дешевое улучшение с самым большим эффектом, потому что сейчас backend открыт для любых внешних запросов.

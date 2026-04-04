# Backend Roadmap

## Current State

Сейчас backend уже умеет:
- создавать anonymous user и выдавать bearer token
- работать только через актуальный auth-flow:
  - `POST /auth/anonymous`
  - `GET /me`
  - `PATCH /me/profile`
  - `PATCH /me/rating`
  - `POST /me/score`
- отдельно включать и выключать участие в рейтинге через `/me/rating`
- отдавать `top 100` только для `score >= 0`
- отдавать `bottom 100` только для `score < 0`
- использовать единый error contract в формате `code + message`
- использовать публичный `camelCase` API contract
- работать на `https://api.wobbly.site`
- публиковать Swagger на `https://api.wobbly.site/api/swagger`
- публиковать человекочитаемую docs page на `https://api.wobbly.site/api/docs`
- обслуживать отдельную admin surface:
  - `https://admin.wobbly.site/production/`
  - `https://admin.wobbly.site/staging/`
- иметь admin auth и роли `owner/admin`
- поддерживать audit log админских действий
- давать self-service смену пароля текущему admin

Инженерная база уже тоже есть:
- backend разнесен на `backend/app/api`, `backend/app/services`, `backend/app/core`, `backend/app/db`, `backend/app/domain`
- frontend вынесен в отдельный `frontend/` подпроект на Vue + TypeScript
- подключен `Alembic`
- добавлены `ruff`, `pytest`, Vue/TypeScript tooling, ESLint, Prettier, pre-commit и pre-push hooks
- есть unit tests и integration tests
- CI/CD уже автоматизирован через GitHub Actions
- production deploy идет через `verify -> deploy`
- staging deploy flow уже подготовлен через `develop -> verify -> deploy-staging`
- базовый anti-abuse слой уже есть на уровне `TrustedHostMiddleware`, CORS и `nginx` rate limiting
- `/ready` уже используется как deploy gate
- public API versioning уже введен через `/api/v1/...`
- real PostgreSQL integration tests уже добавлены в CI

Это уже не просто MVP. Сейчас следующий фокус должен быть не на базовом CRUD, а на надежности, наблюдаемости и эволюции модели данных.

## Active Priorities

Отдельный operational план по защите API:
- `docs/ANTI_ABUSE.md`

### 1. Add score history table

Что сделать:
- добавить таблицу `score_events`
- хранить историю изменений рейтинга:
  - `user_id`
  - `old_score`
  - `new_score`
  - `source`
  - `created_at`
- оставить таблицу `users` как current state

Почему это важно:
- сейчас хранится только текущий `score`
- невозможно разбирать историю изменений, спорные кейсы и аномалии

### 2. Harden score rules

Что сделать:
- явно зафиксировать бизнес-правила для `score`
- определить допустимый диапазон
- решить, можно ли уменьшать `score`
- решить, допустимы ли скачки и перезапись любым значением

Почему это важно:
- сейчас техническая валидация есть, но продуктовая модель рейтинга еще не до конца закреплена

### 3. Add structured logging

Что сделать:
- перейти на структурированные логи
- логировать:
  - `request_id`
  - endpoint
  - status code
  - latency
  - error code

Почему это важно:
- без этого неудобно разбирать инциденты и ошибки мобильной интеграции

### 4. Add uptime monitoring

Что сделать:
- поднять простой мониторинг доступности
- проверять:
  - `https://api.wobbly.site/health`
  - позже `https://api.wobbly.site/ready`
  - `https://wobbly.site`
- завести уведомления о падении

Что использовать:
- `Uptime Kuma` как самый простой старт

Почему это важно:
- сейчас состояние приложения видно в основном вручную
- нужен отдельный сигнал, что API или сайт недоступны

### 5. Add error monitoring

Что сделать:
- подключить Sentry или аналог
- отправлять unhandled exceptions
- отдельно отмечать важные production warnings

Почему это важно:
- сейчас мы видим инциденты в основном через ручную проверку логов

### 6. Add server monitoring

Что сделать:
- собрать базовые серверные метрики:
  - CPU
  - RAM
  - disk
  - restart count
  - nginx errors
- выбрать простой инструмент:
  - `Netdata`
  - или `Grafana + Prometheus` позже

Почему это важно:
- приложение может быть “живым”, но сервер уже деградирует
- это поможет ловить проблемы до падения

### 7. Add automated backups

Что сделать:
- ежедневный `pg_dump`
- хранить несколько последних копий
- выносить backup за пределы сервера

Почему это важно:
- локальные backup-файлы уже делались руками
- нужен системный, повторяемый процесс

### 8. Improve leaderboard queries

Что сделать:
- добавить `offset`
- добавить получение позиции конкретного пользователя
- при необходимости добавить дополнительные режимы leaderboard

Почему это важно:
- текущего `top/bottom limit` хватает для простого экрана
- но API уже упирается в следующий уровень функциональности

### 9. Add anti-fraud and abuse signals

Что сделать:
- логировать подозрительные всплески запросов
- анализировать аномальные прыжки `score`
- при необходимости добавить soft-block или manual review markers

Почему это важно:
- базовый rate limiting уже есть
- следующая ступень это не только ограничение запросов, но и детекция странного поведения

### 10. Add developer ergonomics

Что сделать:
- вынести dev dependencies в отдельный файл или optional extras
- добавить `make`/`just` команды или короткие scripts для частых операций
- упростить bootstrap локальной среды

Почему это важно:
- tooling уже есть
- теперь стоит сделать его проще в использовании для следующего разработчика

### 11. Continue admin console polish

Что сделать:
- добавить change role в owner-only admin management
- улучшить UX screens `Администраторы` / `Профиль`, чтобы не было сценарных дублей
- добавить pagination/filters в audit log
- добавить richer empty/loading/error states

Почему это важно:
- backend foundation уже есть
- дальше основная ценность в удобстве и надежности admin operations

## Suggested Execution Order

### Phase 1
- structured logging

### Phase 2
- uptime monitoring
- server monitoring
- `score_events`
- backups
- anti-fraud signals

### Phase 3
- error monitoring
- richer leaderboard queries

### Phase 4
- developer ergonomics improvements
- admin console polish

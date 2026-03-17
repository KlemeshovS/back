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

Инженерная база уже тоже есть:
- проект разнесен на `app/api`, `app/services`, `app/core`, `app/db`, `app/domain`
- подключен `Alembic`
- добавлены `ruff`, `pytest`, pre-commit и pre-push hooks
- есть unit tests и integration tests
- CI/CD уже автоматизирован через GitHub Actions
- production deploy идет через `verify -> deploy`
- базовый anti-abuse слой уже есть на уровне `TrustedHostMiddleware`, CORS и `nginx` rate limiting

Это уже не просто MVP. Сейчас следующий фокус должен быть не на базовом CRUD, а на надежности, наблюдаемости и эволюции модели данных.

## Active Priorities

Отдельный operational план по защите API:
- `docs/ANTI_ABUSE.md`

### 1. Add readiness endpoint

Что сделать:
- добавить `/ready`
- проверять доступность PostgreSQL
- возвращать понятный статус для production smoke-check и deploy pipeline

Почему это важно:
- сейчас `/health` проверяет только то, что приложение поднялось
- для production и deploy полезнее отличать “процесс жив” от “приложение готово обслуживать запросы”

### 2. Add score history table

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

### 3. Harden score rules

Что сделать:
- явно зафиксировать бизнес-правила для `score`
- определить допустимый диапазон
- решить, можно ли уменьшать `score`
- решить, допустимы ли скачки и перезапись любым значением

Почему это важно:
- сейчас техническая валидация есть, но продуктовая модель рейтинга еще не до конца закреплена

### 4. Add integration tests with real test DB

Что сделать:
- поднять изолированную test PostgreSQL для CI
- добавить сценарии с реальной БД вместо только monkeypatch-based tests
- покрыть:
  - anonymous auth flow
  - profile update
  - rating toggle
  - score update
  - leaderboard queries
  - error scenarios

Почему это важно:
- текущие integration tests уже полезны, но они не ловят проблемы SQL, миграций и реальных DB-paths

### 5. Add structured logging

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

### 6. Add uptime monitoring

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

### 7. Add error monitoring

Что сделать:
- подключить Sentry или аналог
- отправлять unhandled exceptions
- отдельно отмечать важные production warnings

Почему это важно:
- сейчас мы видим инциденты в основном через ручную проверку логов

### 8. Add server monitoring

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

### 9. Add automated backups

Что сделать:
- ежедневный `pg_dump`
- хранить несколько последних копий
- выносить backup за пределы сервера

Почему это важно:
- локальные backup-файлы уже делались руками
- нужен системный, повторяемый процесс

### 10. Improve leaderboard queries

Что сделать:
- добавить `offset`
- добавить получение позиции конкретного пользователя
- при необходимости добавить дополнительные режимы leaderboard

Почему это важно:
- текущего `top/bottom limit` хватает для простого экрана
- но API уже упирается в следующий уровень функциональности

### 11. Introduce API versioning

Что сделать:
- перевести публичный контракт на `/api/v1/...`
- оставить ясный путь для будущих несовместимых изменений

Почему это важно:
- контракт уже живет в мобильном приложении
- дальше breaking changes будут дороже

### 12. Add anti-fraud and abuse signals

Что сделать:
- логировать подозрительные всплески запросов
- анализировать аномальные прыжки `score`
- при необходимости добавить soft-block или manual review markers

Почему это важно:
- базовый rate limiting уже есть
- следующая ступень это не только ограничение запросов, но и детекция странного поведения

### 13. Clean up remaining compatibility wrappers

Что сделать:
- убрать re-export wrappers, если они больше не нужны:
  - `app/auth.py`
  - `app/config.py`
  - `app/database.py`
  - `app/rate_limit.py`
  - `app/schemas.py`

Почему это важно:
- они были полезны на переходном этапе рефакторинга
- дальше лучше оставить одну ясную структуру без дублирующих точек входа

### 14. Add developer ergonomics

Что сделать:
- вынести dev dependencies в отдельный файл или optional extras
- добавить `make`/`just` команды или короткие scripts для частых операций
- упростить bootstrap локальной среды

Почему это важно:
- tooling уже есть
- теперь стоит сделать его проще в использовании для следующего разработчика

## Suggested Execution Order

### Phase 1
- `/ready`
- integration tests with real test DB
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
- cleanup of compatibility wrappers

### Phase 4
- API versioning
- developer ergonomics improvements

## Recommended Next Task

Если выбирать одно следующее улучшение, лучше всего сделать:

`Add readiness endpoint`

Это самый маленький и самый практичный следующий шаг: он сразу улучшит production deploy, monitoring и понимание реальной готовности backend.

## Completed

Ниже задачи, которые уже закрыты и больше не должны висеть в активной части roadmap.

### Security
- done: anonymous auth и bearer token flow
- done: rate limiting для регистрации и обновления рейтинга
- done: базовая input validation для `username` и payload schemas

### API
- done: переход на публичный `camelCase` contract
- done: единый error contract в формате `code + message`
- done: отдельный toggle участия в рейтинге через `PATCH /me/rating`
- done: удалены legacy endpoint'ы:
  - `POST /users/register`
  - `POST /users/score`

### Data / DB
- done: подключен `Alembic`
- done: базовые timestamps уже есть:
  - `created_at`
  - `updated_at`
  - `last_seen_at`

### Reliability / Delivery
- done: настроен GitHub Actions pipeline
- done: автоматизирован deploy после merge в `main`
- done: deploy script обновляет dependencies в production venv
- done: deploy script ждет успешный `/health` перед завершением
- done: `nginx` rate limiting включен для `api.wobbly.site`

### Testing / Tooling
- done: добавлены `ruff` и `pytest`
- done: добавлены unit tests
- done: добавлены integration tests для API routes
- done: добавлены pre-commit и pre-push hooks

### Docs / Process
- done: `/api/docs` и `/api/swagger` разведены по отдельным путям
- done: docs sync включен в CI
- done: при изменении API docs page обновляется в том же изменении
- done: проектный handoff и deploy context зафиксированы в `.md`
- done: non-README docs вынесены в `docs/`

# Rating Service MVP

Backend-репозиторий `Wobbly`:
- `backend/` — FastAPI API, migrations, tests и runtime
- frontend source code живет в отдельном репозитории: [Wobbly-develop/front](https://github.com/Wobbly-develop/front)

Сейчас проект включает:
- API для anonymous auth, профиля и рейтингов
- health и readiness endpoint'ы для monitoring/deploy checks
- admin API и admin UI foundation
- production admin console
- landing page на `https://wobbly.site`
- текстовую docs page на `https://api.wobbly.site/api/docs`
- production deploy через GitHub Actions

## Стек

- FastAPI
- PostgreSQL
- Docker Compose для локальной разработки
- systemd + nginx в production
- GitHub Actions для CI/CD

## Project Structure

Текущая структура проекта:
- `backend/app/main.py` — минимальный entrypoint
- `backend/app/api/app.py` — app factory
- `backend/app/api/dependencies.py` — общие dependencies
- `backend/app/api/routes/` — route modules по зонам ответственности
- `backend/app/core/` — auth, config, rate limiting
- `backend/app/db/` — database access и init_db
- `backend/app/domain/` — Pydantic schemas
- `backend/app/services/` — business logic
- `backend/app/static/` — собранный frontend build, который раздается backend'ом
- `backend/alembic/` — migration scripts
- `scripts/` — CI checks, deploy, docs sync checks
- `.githooks/` — локальные git hooks
- `backend/tests/` — unit и integration tests
- `docs/` — operational, mobile, roadmap и handoff документация
- `.github/workflows/pipeline.yml` — verify + deploy pipeline
- `backend/pyproject.toml` — lint/test tooling config
- frontend source code:
  - [Wobbly-develop/front](https://github.com/Wobbly-develop/front) — landing, privacy, docs и admin UI source code

## Current Project Snapshot

Это актуальная базовая сводка по проекту:
- production API: `https://api.wobbly.site`
- production Swagger: `https://api.wobbly.site/api/swagger`
- production text docs: `https://api.wobbly.site/api/docs`
- production site: `https://wobbly.site`
- продовый сервис: `rating-service.service`
- продовый путь на сервере: `/opt/rating-service`
- reverse proxy в production: `nginx`
- базовый edge-side rate limiting уже включен на `api.wobbly.site`
- основной путь разработки: feature branch -> merge в `develop` -> staging pipeline
- `main` не трогаем по умолчанию; production release делаем только по явной команде пользователя
- production release path: `develop` -> `scripts/prepare_main_release.sh` -> release branch -> `main` -> production pipeline
- ручной deploy через копирование файлов в `/opt/rating-service` и `systemctl restart rating-service` остается fallback-сценарием

Это важно:
- локальный `docker compose` нужен для разработки
- production topology уже другая, и ее не нужно заново угадывать
- точные команды деплоя описаны в `docs/DEPLOY.md`
- отдельная сводка для переноса контекста лежит в `docs/HANDOFF.md`
- staging operational details intentionally documented only in `docs/STAGING.md` on `develop`
- production admin доступна на `https://admin.wobbly.site/production/`
- landing page на `https://wobbly.site` сейчас ведет пользователя в:
  - App Store
  - Google Play
  - Telegram channel
- admin console уже включает:
  - overview
  - users table + context menu actions
  - user edit modal
  - user delete with confirmation
  - admins table + context menu actions
  - admin edit modal
  - admin delete with confirmation
  - owner-only create admin action in table header
  - audit log
  - profile screen with account info only
  - minimal login screen with environment switcher
  - login password visibility toggle by click on eye button
  - role-aware behavior for owner/admin
- первый `owner` bootstrap'ится через env и уже поднят на production:
  - `ADMIN_BOOTSTRAP_LOGIN`
  - `ADMIN_BOOTSTRAP_PASSWORD`
- bootstrap credentials считаем operational secret и не храним в репозитории

## Working Rules

Эти правила нужно считать актуальной базой процесса:
- основная рабочая ветка: `develop`
- `main` обновляем только по явной команде пользователя на production release
- direct merge `develop -> main` больше не используем
- production release делается через `./scripts/prepare_main_release.sh`
- `develop` содержит staging operational context
- `main` должна содержать только production-facing truth
- если меняется API, в том же изменении нужно обновлять:
  - frontend repo: `src/features/docs/content.ts`
  - при необходимости `docs/MOBILE_API.md`
  - при необходимости `README.md`
- перед началом работы всегда сначала проверять:
  - `git status --short --branch`

Минимальный порядок чтения для быстрого входа в проект:
1. `docs/HANDOFF.md`
2. `README.md`
3. `docs/DEPLOY.md`
4. `docs/DEVELOPMENT_WORKFLOW.md`
5. `docs/MOBILE_API.md`

## Docs Page Rule

`https://api.wobbly.site/api/docs` это frontend page, а не серверный шаблон со статическим текстом.

Источник правды:
- frontend repo: `src/features/docs/content.ts`

Что важно помнить:
- build output лежит в `backend/app/static/`
- docs page должна грузить frontend assets через корневые пути `/assets/...`
- если на `/api/docs` белый экран, сначала проверяем загрузку asset-файлов, а не backend route logic

## Release Flow

Production release больше не делается прямым merge `develop -> main`.

Новый flow:
1. завершить работу в `develop`
2. убедиться, что staging-проверка завершена
3. выбрать новую backend version
4. на `develop` запустить `./scripts/prepare_main_release.sh <release-branch> <backend-version>`
5. получить временную release-ветку без staging-only workflow/templates/docs и с новым `backend/VERSION`
6. проверить production-facing docs и surfaces
7. влить release-ветку в `main`
8. production pipeline сам создаст tag `backend/v<version>` и выполнит deploy

### Backend Release Versioning

Для backend теперь есть отдельный release-контур:
- источник правды для версии: `backend/VERSION`
- production tag: `backend/v<version>`
- GitHub Release: `Backend v<version>`
- manual rollback / redeploy workflow: `.github/workflows/deploy-backend-release.yml`
- UI-friendly rollback workflow: `.github/workflows/rollback-backend-release.yml`
- immutable backend archives на сервере сохраняются в `/opt/rating-service/.releases/`
- metadata текущего production deploy пишется в:
  - `/opt/rating-service/.backend-release-version`
  - `/opt/rating-service/.backend-release-ref`
  - `/opt/rating-service/.backend-release-tag`

Это дает:
- понятную backend version для каждого production release
- видимый список backend-версий в GitHub UI на вкладке Releases
- release notes по commit history между backend-тегами
- возможность откатываться на конкретный backend tag или commit
- возможность быстро проверить, какая backend version сейчас реально стоит на production

### Backend Release Checklist

Подготовить production release:

```bash
git checkout develop
git pull
./scripts/prepare_main_release.sh release/main 0.2.0
git status --short --branch
git commit -am "chore(release): prepare backend v0.2.0"
```

После этого:
- проверить release branch
- влить ее в `main`
- дождаться production pipeline

Посмотреть, что сейчас стоит на production:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'cat /opt/rating-service/.backend-release-version && echo "---" && cat /opt/rating-service/.backend-release-tag && echo "---" && cat /opt/rating-service/.backend-release-ref'
```

Откатить backend на конкретную версию:
- открыть GitHub Actions
- для простого rollback выбрать workflow `Rollback Backend Release`
- передать `release_tag`, например `backend/v0.1.0`
- для нестандартного redeploy по commit использовать workflow `Deploy Backend Release`

## API

### Public API Versioning

Новый публичный контракт для клиентов теперь начинается с `/api/v1/...`.

Это значит:
- для новых mobile/web клиентов нужно использовать `https://api.wobbly.site/api/v1`
- текущие unversioned routes пока сохранены для обратной совместимости
- обратно совместимые изменения можно добавлять в `v1`
- любые breaking changes в будущем должны идти через новый namespace, например `/api/v2/...`

### `POST /api/v1/auth/anonymous`

Создает анонимного пользователя и возвращает bearer token.

Response:

```json
{
  "userId": 15,
  "accessToken": "rt_xxxxx",
  "tokenType": "bearer"
}
```

После этого токен надо передавать в заголовке:

```http
Authorization: Bearer rt_xxxxx
```

### `GET /api/v1/me`

Возвращает профиль текущего авторизованного пользователя.

### `PATCH /api/v1/me/profile`

Request:

```json
{
  "username": "player_1",
  "participateInRating": true
}
```

Responses:
- `200` профиль обновлён
- `401` не передан или невалиден bearer token
- `409` такой `username` уже существует
- `422` нельзя включить участие в рейтинге без `username`

### `PATCH /api/v1/me/rating`

Позволяет отдельно включить или выключить участие текущего пользователя в рейтингах.

Request:

```json
{
  "participateInRating": true
}
```

Responses:
- `200` участие в рейтинге обновлено
- `401` не передан или невалиден bearer token
- `422` нельзя включить участие в рейтинге без `username`

### `POST /api/v1/me/score`

Request:

```json
{
  "score": 42
}
```

Responses:
- `200` рейтинг обновлён
- `401` не передан или невалиден bearer token
- `429` слишком много обновлений рейтинга

### `GET /health`

Показывает, что HTTP-приложение запущено и отвечает.

### `GET /ready`

Показывает, что backend реально готов принимать трафик.

Сейчас readiness проверяет доступность PostgreSQL через простой DB ping.

Responses:
- `200` сервис готов
- `503` сервис еще не готов или БД недоступна

## Error Contract

Ошибки API теперь возвращаются в едином формате:

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

### `GET /api/v1/leaderboard/top?limit=100`

Возвращает пользователей с максимальным рейтингом, у которых `score >= 0`.

### `GET /api/v1/leaderboard/bottom?limit=100`

Возвращает пользователей с минимальным рейтингом, у которых `score < 0`.

Подробный мобильный контракт:
- `docs/MOBILE_API.md`
- `https://api.wobbly.site/api/docs`

## Локальный запуск

```bash
cp .env.example .env
docker compose up --build
```

После запуска API будет доступно на:
- `http://localhost:8000`

Frontend source code теперь живет в отдельном репозитории:
- [Wobbly-develop/front](https://github.com/Wobbly-develop/front)

Frontend локально запускается там:

```bash
git clone https://github.com/Wobbly-develop/front.git
cd front
npm ci
npm run dev
```

Полная локальная проверка:

```bash
./scripts/ci_check.sh
```

Она включает:
- `ruff check backend/app backend/tests scripts`
- `pytest`
- frontend checks, если frontend source присутствует в этом репозитории
- `docker compose config`
- docs sync check

Реальные integration tests с PostgreSQL:

```bash
docker compose up -d db
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./.venv/bin/pytest backend/tests/test_api_db_integration.py
```

В CI эти тесты идут через отдельный изолированный PostgreSQL service.

## Локальная разработка

Минимальный рабочий цикл:
1. перейти на `develop`
2. обновить ветку и создать короткоживущую рабочую ветку
3. поднять локальную среду
4. внести изменение
5. прогнать локальные проверки
6. сделать commit
7. вернуть изменения в `develop`

Базовые команды:

```bash
git checkout develop
git pull
git checkout -b feat/my-change
cp .env.example .env
docker compose up --build
```

Frontend в отдельном dev-режиме:

```bash
git clone https://github.com/Wobbly-develop/front.git
cd front
npm ci
npm run dev
```

Backend локально без Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements-dev.txt
uvicorn backend.app.main:app --reload
```

Полезные локальные команды:

```bash
./scripts/ci_check.sh
./scripts/install_git_hooks.sh
docker compose up -d db
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./.venv/bin/pytest backend/tests/test_api_db_integration.py
```

Где что проверять локально:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`
- Frontend dev server: обычно `http://localhost:5173` в отдельном frontend-репозитории

## Docs Rule

Если меняется API, в том же изменении нужно обновлять:
- frontend repo: `src/features/docs/content.ts`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`
- Swagger UI: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`

## Что ещё можно улучшить

- усилить integration tests сценариями с тестовой БД
- добавить readiness endpoint
- добавить structured logging
- добавить fail2ban или Cloudflare как следующий anti-abuse слой

## Development

- workflow: `docs/DEVELOPMENT_WORKFLOW.md`
- production/deploy: `docs/DEPLOY.md`
- database access: `docs/DB_ACCESS.md`
- handoff summary: `docs/HANDOFF.md`
- anti-abuse plan: `docs/ANTI_ABUSE.md`
- backend roadmap: `docs/BACKEND_ROADMAP.md`
- conventions: trunk-based development + Conventional Commits
- branch flow: `develop` для активной разработки, `main` только для production releases по явному запросу
- если задача про admin console, первыми смотреть:
  - frontend repo: `src/pages/AdminPage.vue`
  - frontend repo: `src/features/admin/useAdminConsole.ts`
  - frontend repo: `src/features/admin/api.ts`
  - `backend/app/api/routes/admin.py`
  - `backend/app/services/admin_service.py`
- актуальная рабочая ветка обычно `develop`; не обновлять `main`, если не идет осознанный production release
- если меняется API, нужно обновлять текстовую docs page на `https://api.wobbly.site/api/docs` в том же изменении
- CI дополнительно проверяет, что API-изменения не уходят без обновления `/api/docs`
- linters and tests: `ruff`, `pytest`
- локальные обязательные hooks: `.githooks/pre-commit`, `.githooks/pre-push`
- после рефакторинга новые endpoint changes обычно живут в `backend/app/api/routes/`, `backend/app/services/`, `backend/app/domain/`, `backend/app/core/`
- schema changes теперь должны идти через Alembic migrations

Если меняется поведение API, обычно нужно обновлять:
- frontend repo: `src/features/docs/content.ts`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

Чтобы включить локальные hooks:

```bash
./scripts/install_git_hooks.sh
```

Что делают hooks:
- `pre-commit` — `ruff --fix`, `ruff`, Python syntax, frontend ESLint/Prettier, если frontend source есть в этом репозитории
- `pre-push` — `pytest`, frontend build, если frontend source есть в этом репозитории

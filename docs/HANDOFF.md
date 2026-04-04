# Handoff

Этот файл нужен для быстрого переноса контекста из чата в чат.

Если новый чат должен продолжить работу по проекту, начинать нужно с этого файла, а не с повторного исследования репозитория и production.

## Project Snapshot

- repository: `https://github.com/Wobbly-develop/wobbly_back`
- main site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`
- expected active development branch: `develop`

Если задача переносится в новый чат, это нужно считать рабочей правдой без повторного расследования.

## Current Production Truth

Это уже подтвержденные факты:
- production path: `/opt/rating-service`
- live service: `rating-service.service`
- reverse proxy: `nginx`
- базовый `nginx` rate limiting уже включен на `api.wobbly.site`
- app process: `uvicorn` behind systemd
- SSH access: `root@api.wobbly.site` через локальный `deploy_key`
- рабочий пользователь приложения: `ratingapp`

Важно для веток:
- `develop` содержит production и staging operational context
- `main` должна содержать только production-facing truth
- staging operational details держим в `docs/STAGING.md` и develop-only артефактах
- production release теперь готовится через release-ветку, а не через прямой merge `develop -> main`

Admin baseline в коде уже есть:
- admin UI route для production: `/production/` на `admin.wobbly.site`
- admin API routes: `/admin/...`
- первый owner создается через env bootstrap:
  - `ADMIN_BOOTSTRAP_LOGIN`
  - `ADMIN_BOOTSTRAP_PASSWORD`
- admin host уже поднят на `https://admin.wobbly.site`
- production admin URL: `https://admin.wobbly.site/production/`
- same-origin admin API для production идет через:
  - `/production/api/...`
- admin frontend assets идут через:
  - `/assets/...`
  - `/og/...`
- owner bootstrap уже применен на production
- staging admin details intentionally live outside production handoff
- bootstrap credentials это operational secret; в репозиторий их не кладем

Landing baseline:
- production landing: `https://wobbly.site`
- текущие production CTA на landing:
  - App Store
  - Google Play
  - Telegram
- в последних правках с landing убраны блоки:
  - `О продукте`
  - `Три быстрых шага`

Важно:
- production сейчас не живет через `docker compose up`
- production сейчас не живет как git checkout на сервере
- не нужно начинать с поиска по `/etc`, `/opt`, `/srv`, если нет явного повода

## Current Architecture

Репозиторий теперь разделен на два подпроекта:
- `backend/`
  - `backend/app/main.py` — минимальный entrypoint
  - `backend/app/api/` — app factory, dependencies, routes
  - `backend/app/services/` — business logic
  - `backend/app/core/` — auth, config, rate limiting
  - `backend/app/db/database.py` — DB access
  - `backend/app/domain/schemas.py` — Pydantic schemas
  - `backend/alembic/` — migrations
  - `backend/tests/` — unit и integration tests
- `frontend/`
  - `frontend/src/pages/` — landing, privacy, docs, admin screens
  - `frontend/src/features/docs/content.ts` — источник правды для `/api/docs`
  - `frontend/src/features/admin/` — admin console state и typed API client
  - `frontend/package.json` — Vite, Vue, TypeScript, ESLint, Prettier

Backend продолжает раздавать собранный frontend build из `backend/app/static`.

## API State

Актуальные основные endpoint'ы:
- `GET /health`
- `GET /ready`
- `POST /api/v1/auth/anonymous`
- `GET /api/v1/me`
- `PATCH /api/v1/me/profile`
- `PATCH /api/v1/me/rating`
- `POST /api/v1/me/score`
- `GET /api/v1/leaderboard/top`
- `GET /api/v1/leaderboard/bottom`
- `POST /admin/auth/login`
- `POST /admin/auth/logout`
- `GET /admin/me`
- `PATCH /admin/me/password`
- `GET /admin/overview`
- `GET /admin/users`
- `GET /admin/users/{id}`
- `PATCH /admin/users/{id}`
- `DELETE /admin/users/{id}`
- `GET /admin/admin-users`
- `POST /admin/admin-users`
- `PATCH /admin/admin-users/{id}`
- `DELETE /admin/admin-users/{id}`

Текущее поведение leaderboard:
- `top` возвращает только пользователей с `score >= 0`
- `bottom` возвращает только пользователей с `score < 0`

Versioning rule:
- `v1` — текущий стабильный public contract
- legacy unversioned routes пока остаются как compatibility layer
- breaking changes нельзя вносить в `v1` без нового version namespace вроде `/api/v2/...`

Completed platform decisions:
- `/ready` уже является deploy gate
- public API versioning уже введен через `/api/v1/...`
- real PostgreSQL integration tests уже добавлены в CI

## Docs Rule

Если меняется API, в том же изменении нужно обновлять:
- `frontend/src/features/docs/content.ts`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

Ошибки API теперь стандартизированы:
- формат ответа: `code + message`

Источник правды для человекочитаемой API docs page:
- `frontend/src/features/docs/content.ts`

Важно:
- `/api/docs` это frontend route
- если docs page белая, сначала проверяем asset loading
- корректные asset paths для docs page должны идти через `/assets/...`, а не `/api/assets/...`

Admin UI файлы:
- `frontend/src/pages/AdminPage.vue`
- `frontend/src/features/admin/useAdminConsole.ts`
- `frontend/src/features/admin/api.ts`

Admin UI сейчас уже умеет:
- sidebar navigation по экранам
- topbar environment switcher logic exists in develop, but production handoff should treat `/production/` as the only production-facing admin surface
- overview screen
- users table + context menu actions
- user edit modal
- user delete with confirmation
- admins table + context menu actions
- admin edit modal
- admin delete with confirmation
- owner-only create admin action in table header
- audit log screen
- profile screen только с информацией об аккаунте
- login screen без лишних заголовков
- login screen с environment switcher
- password visibility toggle на login screen по клику на глазик
- role-aware поведение:
  - owner видит экран и управление `Администраторы`
  - обычный `admin` не должен видеть owner-only controls
- операционное правило UI:
  - self-service смены пароля в текущем UI сейчас нет, хотя backend endpoint `PATCH /admin/me/password` пока существует
  - экран `Администраторы` нужен для управления другими admin-аккаунтами

Текущее локальное состояние рабочей директории:
- current branch: `develop`
- перед продолжением всегда сначала проверять `git status --short --branch`
- если `git status` чистый и активная ветка `develop`, можно продолжать работу без дополнительных уточнений

Важно:
- `/api/docs` собирается frontend приложением на Vue
- при сыром `curl` в HTML не всегда будут видны финальные тексты
- если нужно проверить содержимое docs page, сначала смотри `frontend/src/features/docs/content.ts`

## Testing And Tooling

Сейчас в проекте уже есть:
- `ruff`
- `pytest`
- `Vue 3 + TypeScript`
- `ESLint`
- `Prettier`
- unit tests:
  - `backend/tests/test_auth.py`
  - `backend/tests/test_rate_limit.py`
  - `backend/tests/test_schemas.py`
- integration tests:
  - `backend/tests/test_api_endpoints.py`
  - `backend/tests/test_api_db_integration.py`

Tooling config:
- `backend/pyproject.toml`
- `frontend/package.json`

## CI/CD

Основной flow:
1. разработка идет в короткой ветке
2. merge в `develop`
3. GitHub Actions на `develop` гоняет staging verify/deploy flow
4. когда пользователь явно запрашивает production release, из `develop` готовится release-ветка через `scripts/prepare_main_release.sh`
5. release-ветка вливается в `main`
6. GitHub Actions запускает `.github/workflows/pipeline.yml`
7. `deploy` выкатывает на production после зеленого `verify`

Локальные скрипты, на которые опирается pipeline:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`

Ветки по окружениям:
- `develop` — основная разработка и staging
- release branch — временная production-prep ветка без staging-only хвостов
- `main` — production-only branch, которую обновляем только по явной команде пользователя

Release rule:
- `main` не должна получать staging-only workflow, staging docs и staging infra templates
- для production release сначала готовим release branch через `scripts/prepare_main_release.sh`
- если в `main` внезапно есть staging-specific truth, это drift, а не норма

Backend release versioning:
- источник правды для backend version: `backend/VERSION`
- production pipeline создает tag `backend/v<version>` на merge commit в `main`
- rollback / redeploy конкретной backend version делается через `.github/workflows/deploy-backend-release.yml`
- текущая production backend version на сервере должна писаться в:
  - `/opt/rating-service/.backend-release-version`
  - `/opt/rating-service/.backend-release-ref`
  - `/opt/rating-service/.backend-release-tag`

Нюанс docs sync check:
- в GitHub Actions `verify` использует полный fetch history
- если `base sha` все равно недоступен локально, `scripts/check_api_docs_sync.sh` пропускает проверку вместо `fatal: bad object`

Локальные guardrails перед коммитом:
- `.githooks/pre-commit`
- `.githooks/pre-push`
- `scripts/pre_commit_check.sh`
- `scripts/pre_push_check.sh`
- `scripts/install_git_hooks.sh`

Секреты GitHub Actions уже заведены:
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PATH`
- `DEPLOY_SERVICE`
- `DEPLOY_OWNER`
- `DEPLOY_VENV_PATH`
- `DEPLOY_SSH_KEY`

Во время production deploy:
- release архив распаковывается в `/opt/rating-service`
- затем обновляются Python dependencies в server venv
- только после этого перезапускается `rating-service.service`
- deploy считается успешным только если поднялся локальный `/ready`

Для текущего production:
- `DEPLOY_VENV_PATH=/opt/rating-service/.venv`

Healthcheck URL в workflow теперь зафиксирован в коде:
- production deploy gate: `http://127.0.0.1:8000/ready`

Staging-specific secrets и operational details смотри только в `docs/STAGING.md` на ветке `develop`.

Типовая проблема:
- `Load key ... error in libcrypto`

Обычно это значит:
- в `DEPLOY_SSH_KEY` вставлен не приватный ключ
- или он вставлен без нормальных переносов строк

## What To Read First In A New Chat

Порядок чтения:
1. `docs/HANDOFF.md`
2. `README.md`
3. `docs/DEPLOY.md`
4. `docs/DB_ACCESS.md`
5. `docs/DEVELOPMENT_WORKFLOW.md`
6. `docs/MOBILE_API.md`
7. `docs/BACKEND_ROADMAP.md`
8. если задача про защиту API: `docs/ANTI_ABUSE.md`

Если задача про staging:
- читать `docs/STAGING.md`, но только на ветке `develop`

## Recommended First Commands

Если новый чат продолжает работу:
1. `git status --short --branch`
2. если задача про production: прочитать `docs/DEPLOY.md`
3. если задача про API: прочитать `docs/MOBILE_API.md` и посмотреть `frontend/src/features/docs/content.ts`
4. если задача про админку: сначала смотреть:
   - `frontend/src/pages/AdminPage.vue`
   - `frontend/src/features/admin/useAdminConsole.ts`
   - `frontend/src/features/admin/api.ts`
   - `backend/app/api/routes/admin.py`
   - `backend/app/services/admin_service.py`
   - потом уже только при необходимости `frontend/src/features/docs/content.ts`, `README.md`, `docs/DEPLOY.md`
5. если задача про архитектуру: смотреть `backend/app/api/`, `backend/app/services/`, `backend/app/core/`, `backend/app/domain/`, `backend/app/db/`

## Current Next Improvements

Самые логичные следующие технические шаги:
- uptime monitoring for `/health` and `/ready`
- richer integration tests with test DB
- structured logging
- Sentry or similar error monitoring
- server monitoring for CPU/RAM/disk
- fail2ban for repeated 401/429 abuse

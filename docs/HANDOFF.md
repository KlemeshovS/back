# Handoff

Этот файл нужен для быстрого переноса контекста из чата в чат.

Если новый чат должен продолжить работу по проекту, начинать нужно с этого файла, а не с повторного исследования репозитория и production.

## Project Snapshot

- repository: `https://github.com/KlemeshovS/wobbly_back`
- main site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`
- expected active development branch: `develop`

## Current Production Truth

Это уже подтвержденные факты:
- production path: `/opt/rating-service`
- live service: `rating-service.service`
- reverse proxy: `nginx`
- базовый `nginx` rate limiting уже включен на `api.wobbly.site`
- app process: `uvicorn` behind systemd
- SSH access: `root@api.wobbly.site` через локальный `deploy_key`
- рабочий пользователь приложения: `ratingapp`

Staging baseline тоже уже поднят:
- staging path: `/opt/rating-service-staging`
- staging service: `rating-service-staging.service`
- staging DB: `app_staging`
- staging nginx protection идет через `X-Staging-Key`
- staging workflow лежит в `.github/workflows/staging.yml`
- staging public URL: `https://staging-api.wobbly.site`
- staging HTTPS уже поднят через `certbot --nginx`

Admin baseline в коде уже есть:
- admin UI routes: `/production/` и `/staging/` на `admin.wobbly.site`
- admin API routes: `/admin/...`
- первый owner создается через env bootstrap:
  - `ADMIN_BOOTSTRAP_LOGIN`
  - `ADMIN_BOOTSTRAP_PASSWORD`
- admin host уже поднят на `https://admin.wobbly.site`
- `admin.wobbly.site/production/` проксируется в production app
- `admin.wobbly.site/staging/` проксируется в staging app
- same-origin admin API идет через:
  - `/production/api/...`
  - `/staging/api/...`
- admin frontend assets идут через:
  - `/assets/...`
  - `/og/...`
- owner bootstrap уже применен на production и staging
- staging CORS уже разрешает `https://admin.wobbly.site`
- bootstrap credentials это operational secret; в репозиторий их не кладем

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

Compatibility wrappers пока оставлены:
- `backend/app/auth.py`
- `backend/app/config.py`
- `backend/app/database.py`
- `backend/app/rate_limit.py`
- `backend/app/schemas.py`

## API State

Актуальные основные endpoint'ы:
- `POST /auth/anonymous`
- `GET /me`
- `PATCH /me/profile`
- `PATCH /me/rating`
- `POST /me/score`
- `GET /leaderboard/top`
- `GET /leaderboard/bottom`
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

## Docs Rule

Если меняется API, в том же изменении нужно обновлять:
- `frontend/src/features/docs/content.ts`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

Ошибки API теперь стандартизированы:
- формат ответа: `code + message`

Источник правды для человекочитаемой API docs page:
- `frontend/src/features/docs/content.ts`

Admin UI файлы:
- `frontend/src/pages/AdminPage.vue`
- `frontend/src/features/admin/useAdminConsole.ts`
- `frontend/src/features/admin/api.ts`

Admin UI сейчас уже умеет:
- sidebar navigation по экранам
- topbar environment switcher `production/staging`
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

Tooling config:
- `backend/pyproject.toml`
- `frontend/package.json`

## CI/CD

Основной flow:
1. разработка идет в короткой ветке
2. merge в `develop`
3. GitHub Actions запускает `.github/workflows/staging.yml`
4. `verify` гоняет проверки
5. `deploy-staging` выкатывает изменения в staging после зеленого `verify`
6. когда пользователь явно запрашивает production release, `develop` вливается в `main`
7. GitHub Actions запускает `.github/workflows/pipeline.yml`
8. `deploy` выкатывает на production после зеленого `verify`

Локальные скрипты, на которые опирается pipeline:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`

Ветки по окружениям:
- `develop` — основная разработка и staging
- `main` — production release branch, которую обновляем только по явной команде пользователя

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
- deploy считается успешным только если поднялся локальный `/health`

Для текущего production:
- `DEPLOY_VENV_PATH=/opt/rating-service/.venv`

Для staging workflow нужны отдельные secrets:
- `STAGING_DEPLOY_HOST`
- `STAGING_DEPLOY_USER`
- `STAGING_DEPLOY_PATH`
- `STAGING_DEPLOY_SERVICE`
- `STAGING_DEPLOY_OWNER`
- `STAGING_DEPLOY_VENV_PATH`
- `STAGING_DEPLOY_HEALTHCHECK_URL`
- `STAGING_DEPLOY_SSH_KEY`
- `STAGING_PUBLIC_BASE_URL`
- `STAGING_ACCESS_KEY`

Текущее ожидаемое наполнение staging secrets:
- `STAGING_DEPLOY_HOST=api.wobbly.site`
- `STAGING_DEPLOY_USER=root`
- `STAGING_DEPLOY_PATH=/opt/rating-service-staging`
- `STAGING_DEPLOY_SERVICE=rating-service-staging`
- `STAGING_DEPLOY_OWNER=ratingapp:ratingapp`
- `STAGING_DEPLOY_VENV_PATH=/opt/rating-service-staging/.venv`
- `STAGING_DEPLOY_HEALTHCHECK_URL=http://127.0.0.1:8001/health`
- `STAGING_PUBLIC_BASE_URL=https://staging-api.wobbly.site`
- `STAGING_ACCESS_KEY=<shared secret value>`

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
- readiness endpoint `/ready`
- uptime monitoring for `/health` and `/ready`
- richer integration tests with test DB
- structured logging
- Sentry or similar error monitoring
- server monitoring for CPU/RAM/disk
- fail2ban for repeated 401/429 abuse

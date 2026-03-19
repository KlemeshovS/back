# Handoff

Этот файл нужен для быстрого переноса контекста из чата в чат.

Если новый чат должен продолжить работу по проекту, начинать нужно с этого файла, а не с повторного исследования репозитория и production.

## Project Snapshot

- repository: `https://github.com/KlemeshovS/wobbly_back`
- main site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`

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

Важно:
- production сейчас не живет через `docker compose up`
- production сейчас не живет как git checkout на сервере
- не нужно начинать с поиска по `/etc`, `/opt`, `/srv`, если нет явного повода

## Current Architecture

Структура после второго этапа рефакторинга:
- `app/main.py` — минимальный entrypoint
- `app/api/app.py` — app factory
- `app/api/dependencies.py` — dependencies
- `app/api/routes/`:
  - `auth.py`
  - `profile.py`
  - `leaderboard.py`
  - `docs.py`
  - `site.py`
  - `health.py`
- `app/services/user_service.py` — business logic
- `app/core/` — auth, config, rate limiting
- `app/db/database.py` — DB access
- `app/domain/schemas.py` — Pydantic schemas
- `app/static/` — landing page, docs page, css, js, assets
- `alembic/` — migration scripts

Compatibility wrappers пока оставлены:
- `app/auth.py`
- `app/config.py`
- `app/database.py`
- `app/rate_limit.py`
- `app/schemas.py`

## API State

Актуальные основные endpoint'ы:
- `POST /auth/anonymous`
- `GET /me`
- `PATCH /me/profile`
- `PATCH /me/rating`
- `POST /me/score`
- `GET /leaderboard/top`
- `GET /leaderboard/bottom`

Текущее поведение leaderboard:
- `top` возвращает только пользователей с `score >= 0`
- `bottom` возвращает только пользователей с `score < 0`

## Docs Rule

Если меняется API, в том же изменении нужно обновлять:
- `app/static/js/api-docs.js`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

Ошибки API теперь стандартизированы:
- формат ответа: `code + message`

Источник правды для человекочитаемой API docs page:
- `app/static/js/api-docs.js`

Важно:
- `/api/docs` собирается клиентским JavaScript
- при сыром `curl` в HTML не всегда будут видны финальные тексты
- если нужно проверить содержимое docs page, сначала смотри `app/static/js/api-docs.js`

## Testing And Tooling

Сейчас в проекте уже есть:
- `ruff`
- `pytest`
- unit tests:
  - `tests/test_auth.py`
  - `tests/test_rate_limit.py`
  - `tests/test_schemas.py`
- integration tests:
  - `tests/test_api_endpoints.py`

Tooling config:
- `pyproject.toml`

## CI/CD

Основной flow:
1. разработка идет в короткой ветке
2. merge в `develop`
3. GitHub Actions запускает `.github/workflows/staging.yml`
4. `verify` гоняет проверки
5. `deploy-staging` выкатывает изменения в staging после зеленого `verify`
6. когда нужен production release, `develop` вливается в `main`
7. GitHub Actions запускает `.github/workflows/pipeline.yml`
8. `deploy` выкатывает на production после зеленого `verify`

Локальные скрипты, на которые опирается pipeline:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`

Ветки по окружениям:
- `develop` — основная разработка и staging
- `main` — production release branch

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
3. если задача про API: прочитать `docs/MOBILE_API.md` и посмотреть `app/static/js/api-docs.js`
4. если задача про архитектуру: смотреть `app/api/`, `app/services/`, `app/core/`, `app/domain/`, `app/db/`

## Current Next Improvements

Самые логичные следующие технические шаги:
- readiness endpoint `/ready`
- uptime monitoring for `/health` and `/ready`
- richer integration tests with test DB
- structured logging
- Sentry or similar error monitoring
- server monitoring for CPU/RAM/disk
- fail2ban for repeated 401/429 abuse

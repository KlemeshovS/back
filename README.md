# Wobbly Back

Backend-репозиторий проекта `Wobbly`.

Репозитории:
- backend: [Wobbly-develop/back](https://github.com/Wobbly-develop/back)
- frontend: [Wobbly-develop/front](https://github.com/Wobbly-develop/front)

Этот репозиторий отвечает за:
- FastAPI API
- PostgreSQL schema и Alembic migrations
- backend tests и CI
- production/staging deploy backend
- release tags и rollback backend
- раздачу уже собранного frontend bundle из `backend/app/static`

## Что здесь есть

- `backend/app/main.py` — entrypoint
- `backend/app/api/` — app factory, dependencies, routes
- `backend/app/services/` — бизнес-логика
- `backend/app/domain/` — Pydantic schemas
- `backend/app/core/` — auth, config, rate limiting, shared helpers
- `backend/app/db/` — database access и startup DB init
- `backend/app/static/` — текущий собранный frontend bundle
- `backend/alembic/` — migrations
- `backend/tests/` — backend tests
- `scripts/` — checks, deploy, release helpers
- `docs/` — backend operational docs

## Что вынесено в другой репозиторий

Frontend source code живет в [Wobbly-develop/front](https://github.com/Wobbly-develop/front).

Там находятся:
- landing
- privacy
- text docs page source
- admin UI source

Если в backend-доках встречаются ссылки на `frontend/...`, их нужно читать как пути внутри frontend-репозитория.

## Локальный запуск

Через Docker Compose:

```bash
cp .env.example .env
docker compose up --build
```

После запуска:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`

Без Docker:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn backend.app.main:app --reload
```

## Проверки

Полный локальный прогон:

```bash
./scripts/ci_check.sh
```

Он включает:
- Python syntax checks
- `ruff`
- `pytest`
- `docker compose config`
- API docs sync check
- frontend checks только если frontend source временно присутствует в этом репозитории

Реальные DB integration tests:

```bash
docker compose up -d db
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./.venv/bin/pytest backend/tests/test_api_db_integration.py
```

## Branch Flow

- `develop` — основная ветка разработки
- `main` — production-only ветка
- staging живет на `develop`
- production release делается через release branch, а не прямым `develop -> main`

Production release path:
1. закончить работу в `develop`
2. выбрать новую backend version в `backend/VERSION`
3. запустить `./scripts/prepare_main_release.sh <release-branch> <backend-version>`
4. проверить release branch
5. влить release branch в `main`
6. дождаться production pipeline

## Backend Release Versioning

- backend version хранится в `backend/VERSION`
- production tag: `backend/v<version>`
- GitHub Release: `Backend v<version>`
- rollback через GitHub Actions workflow `Rollback Backend Release`
- ручной redeploy по ref через `Deploy Backend Release`

## Production URLs

- site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`
- admin: `https://admin.wobbly.site/production/`

## Важные docs

- [docs/HANDOFF.md](/Users/klem/Documents/eguene/docs/HANDOFF.md)
- [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
- [docs/DEVELOPMENT_WORKFLOW.md](/Users/klem/Documents/eguene/docs/DEVELOPMENT_WORKFLOW.md)
- [docs/MOBILE_API.md](/Users/klem/Documents/eguene/docs/MOBILE_API.md)
- [docs/STAGING.md](/Users/klem/Documents/eguene/docs/STAGING.md)

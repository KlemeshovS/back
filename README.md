# Wobbly Back

Backend-репозиторий проекта `Wobbly`.

Репозитории:
- backend: [Wobbly-develop/back](https://github.com/Wobbly-develop/back)
- frontend: [Wobbly-develop/front](https://github.com/Wobbly-develop/front)

Здесь живут:
- FastAPI API
- PostgreSQL schema и Alembic migrations
- backend tests и CI
- production/staging deploy backend
- backend release versioning, tags и rollback

## Структура

- `backend/app/main.py` — entrypoint
- `backend/app/api/` — routes, app factory, dependencies
- `backend/app/services/` — бизнес-логика
- `backend/app/domain/` — Pydantic schemas
- `backend/app/core/` — config, auth, errors, helpers
- `backend/app/db/` — database access
- `backend/alembic/` — migrations
- `backend/tests/` — тесты
- `scripts/` — checks, deploy, release helpers
- `docs/` — только нужные backend docs

## Frontend живет отдельно

Исходники landing, docs page и admin UI находятся в [Wobbly-develop/front](https://github.com/Wobbly-develop/front).

В этом репозитории frontend не разрабатывается и не деплоится. На сервере backend и frontend должны жить раздельно:
- production backend: `/opt/rating-service`
- staging backend: `/opt/rating-service-staging`
- production frontend: `/opt/wobbly-front-production/current`
- staging frontend: `/opt/wobbly-front-staging/current`

## Быстрый старт

### Вариант 1. Через Docker

```bash
cp .env.example .env
docker compose up --build
```

После запуска:
- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/api/swagger`
- Text docs: `http://localhost:8000/api/docs`

### Вариант 2. Без Docker

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
export DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app
cd backend
uvicorn app.main:app --reload
```

Для локальной базы можно поднять только Postgres:

```bash
docker compose up -d db
```

Если база запускается первый раз, миграции применятся на старте приложения автоматически.

## Как разрабатывать локально

Обычный цикл:
1. создать ветку от `develop`
2. поднять локальную БД
3. запустить API
4. внести изменения
5. прогнать проверки
6. сделать commit и push

Главная команда проверок:

```bash
./scripts/ci_check.sh
```

Она запускает:
- Python syntax checks
- `ruff format --check`
- `ruff check`
- `pytest`
- `docker compose config`
- API docs sync check

Поштучно:

```bash
./scripts/format_check.sh
./scripts/lint.sh
./scripts/test.sh
```

Точечный прогон real DB integration tests:

```bash
docker compose up -d db
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./.venv/bin/pytest backend/tests/test_api_db_integration.py
```

Git hooks:

```bash
./scripts/install_git_hooks.sh
```

## Release flow

- `develop` — основная ветка разработки
- `main` — production-only ветка
- production release делается через release branch, а не прямым `develop -> main`

Путь релиза:
1. закончить работу в `develop`
2. обновить `backend/VERSION`
3. запустить `./scripts/prepare_main_release.sh <release-branch> <backend-version>`
4. проверить release branch
5. влить release branch в `main`
6. дождаться production pipeline

## Версии и rollback

- версия backend хранится в `backend/VERSION`
- production tag: `backend/v<version>`
- GitHub Release: `Backend v<version>`
- rollback: GitHub Actions -> `Rollback Backend Release`
- ручной redeploy по ref: `Deploy Backend Release`

## Production URLs

- site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`
- admin: `https://admin.wobbly.site/production/`

Важно:
- `wobbly.site`, `/api/docs` и `admin` теперь раздаются nginx напрямую из frontend deploy dirs
- backend отвечает только за API и admin API routes

## Что читать дальше

- [docs/HANDOFF.md](/Users/klem/Documents/eguene/docs/HANDOFF.md)
- [docs/DEVELOPMENT_WORKFLOW.md](/Users/klem/Documents/eguene/docs/DEVELOPMENT_WORKFLOW.md)
- [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
- [docs/MOBILE_API.md](/Users/klem/Documents/eguene/docs/MOBILE_API.md)
- [docs/TECHNICAL_BACKLOG.md](/Users/klem/Documents/eguene/wobbly/back/docs/TECHNICAL_BACKLOG.md)

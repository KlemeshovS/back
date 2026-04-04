# Handoff

Этот файл нужен для быстрого старта нового чата именно по backend-репозиторию.

## Репозитории

- backend: `https://github.com/Wobbly-develop/back`
- frontend: `https://github.com/Wobbly-develop/front`

Важно:
- frontend source code больше не живет в backend-репозитории
- если нужно менять landing, docs page или admin UI source, идти нужно в frontend-репозиторий
- backend-репозиторий хранит только собранный bundle в `backend/app/static`

## Быстрая правда по проекту

- production API: `https://api.wobbly.site`
- production site: `https://wobbly.site`
- production admin: `https://admin.wobbly.site/production/`
- production path: `/opt/rating-service`
- production service: `rating-service.service`
- reverse proxy: `nginx`
- active development branch: `develop`

## Что считается source of truth

- backend code: этот репозиторий
- frontend source: `Wobbly-develop/front`
- production deploy details: [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
- release/process rules: [docs/DEVELOPMENT_WORKFLOW.md](/Users/klem/Documents/eguene/docs/DEVELOPMENT_WORKFLOW.md)
- mobile contract: [docs/MOBILE_API.md](/Users/klem/Documents/eguene/docs/MOBILE_API.md)

## Backend release flow

Production release:
1. работа идет в `develop`
2. перед релизом меняется `backend/VERSION`
3. запускается `./scripts/prepare_main_release.sh <release-branch> <backend-version>`
4. release branch вливается в `main`
5. `main` pipeline создает tag `backend/v<version>` и GitHub Release
6. deploy идет через GitHub Actions

Rollback:
- GitHub Actions -> `Rollback Backend Release`
- tag вида `backend/v0.2.0`

## Что не нужно переисследовать

- production path уже известен: `/opt/rating-service`
- production service уже известен: `rating-service.service`
- deploy идет через GitHub Actions
- readiness gate: `/ready`
- backend versioning уже включен

## Если задача про frontend

Идти в `https://github.com/Wobbly-develop/front`.

Смотреть в первую очередь:
- `src/pages/LandingPage.vue`
- `src/pages/ApiDocsPage.vue`
- `src/pages/AdminPage.vue`
- `src/features/docs/content.ts`
- `src/features/admin/`

## Если задача про backend

Смотреть в первую очередь:
- `backend/app/api/routes/`
- `backend/app/services/`
- `backend/app/domain/`
- `backend/app/core/`
- `backend/tests/`

## Перед началом работы

1. Прочитать этот файл
2. Прочитать [README.md](/Users/klem/Documents/eguene/README.md)
3. Если задача про production, прочитать [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
4. Проверить `git status --short --branch`

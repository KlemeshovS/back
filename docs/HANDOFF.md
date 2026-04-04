# Handoff

Быстрый старт для нового человека в backend-репозитории.

## Репозитории

- backend: `https://github.com/Wobbly-develop/back`
- frontend: `https://github.com/Wobbly-develop/front`

Frontend source больше не живет здесь. Если задача про landing, docs page или admin UI, нужно идти во frontend-репозиторий.

## Самое важное

- production API: `https://api.wobbly.site`
- production site: `https://wobbly.site`
- production admin: `https://admin.wobbly.site/production/`
- production path: `/opt/rating-service`
- production service: `rating-service.service`
- reverse proxy: `nginx`
- основная ветка разработки: `develop`

## Что читать

1. [README.md](/Users/klem/Documents/eguene/README.md)
2. [docs/DEVELOPMENT_WORKFLOW.md](/Users/klem/Documents/eguene/docs/DEVELOPMENT_WORKFLOW.md)
3. [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
4. [docs/MOBILE_API.md](/Users/klem/Documents/eguene/docs/MOBILE_API.md)

## Где искать код

Сначала смотреть:
- `backend/app/api/routes/`
- `backend/app/services/`
- `backend/app/domain/`
- `backend/app/core/`
- `backend/tests/`

## Release и rollback

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

## Что уже известно и не надо переоткрывать

- production path: `/opt/rating-service`
- production service: `rating-service.service`
- deploy идет через GitHub Actions
- readiness gate: `/ready`
- backend versioning уже включен

## Перед началом работы

1. проверить `git status --short --branch`
2. убедиться, что вы на нужной ветке
3. поднять локальную БД и backend по `README.md`

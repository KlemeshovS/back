# Handoff

Быстрый старт для нового человека в backend-репозитории.

## Репозитории

- backend: `https://github.com/Wobbly-develop/back`
- frontend: `https://github.com/Wobbly-develop/front`

Frontend source больше не живет здесь. Если задача про landing, docs page или admin UI, нужно идти во frontend-репозиторий.
На сервере frontend тоже должен жить отдельно от backend:
- backend: `/opt/rating-service`
- production frontend: `/opt/wobbly-front-production/current`
- staging frontend: `/opt/wobbly-front-staging/current`

## Самое важное

- production API: `https://api.wobbly.site`
- production site: `https://wobbly.site`
- production admin: `https://admin.wobbly.site/production/`
- production path: `/opt/rating-service`
- production service: `rating-service.service`
- reverse proxy: `nginx`
- основная ветка разработки: `develop`
- в `main` идем только по прямой просьбе владельца
- любой push в `main` считается релизом

## Что читать

1. [README.md](/Users/klem/Documents/eguene/README.md)
2. [docs/DEVELOPMENT_WORKFLOW.md](/Users/klem/Documents/eguene/docs/DEVELOPMENT_WORKFLOW.md)
3. [docs/DEPLOY.md](/Users/klem/Documents/eguene/docs/DEPLOY.md)
4. [docs/MOBILE_API.md](/Users/klem/Documents/eguene/docs/MOBILE_API.md)
5. [docs/SOCIAL_AUTH_MODEL.md](/Users/klem/Documents/eguene/wobbly/back/docs/SOCIAL_AUTH_MODEL.md)
6. [docs/UPTIME_MONITORING.md](/Users/klem/Documents/eguene/wobbly/back/docs/UPTIME_MONITORING.md)

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
5. `main` pipeline создает release tag:
   - сначала `backend/v<version>`
   - если он уже занят другим коммитом, автоматически `backend/v<version>-r1`, затем `-r2` и так далее
   и после этого создает GitHub Release
6. deploy идет через GitHub Actions

Rollback:
- GitHub Actions -> `Rollback Backend Release`
- tag вида `backend/v0.2.0` или `backend/v0.2.0-r1`

## Что уже известно и не надо переоткрывать

- production path: `/opt/rating-service`
- production service: `rating-service.service`
- deploy идет через GitHub Actions
- readiness gate: `/ready`
- backend versioning уже включен
- uptime monitoring стартово разворачивается через `Uptime Kuma`

## Перед началом работы

1. проверить `git status --short --branch`
2. убедиться, что обычная работа идет в `develop`
3. поднять локальную БД и backend по `README.md`

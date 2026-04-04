# Staging

Staging operational doc. Этот файл нужен только на `develop`.

Если он попал в `main`, release flow сломан.

## Базовые параметры

- staging path: `/opt/rating-service-staging`
- staging service: `rating-service-staging.service`
- staging DB: `app_staging`
- staging port: `8001`
- staging public URL: `https://staging-api.wobbly.site`
- staging nginx protection: `X-Staging-Key`
- staging workflow: `.github/workflows/staging.yml`

## Staging admin

- UI: `https://admin.wobbly.site/staging/`
- same-origin admin API: `/staging/api/...`
- staging frontend deploy dir: `/opt/wobbly-front-staging/current`

## Staging secrets

- `STAGING_DEPLOY_HOST`
- `STAGING_DEPLOY_USER`
- `STAGING_DEPLOY_PATH`
- `STAGING_DEPLOY_SERVICE`
- `STAGING_DEPLOY_OWNER`
- `STAGING_DEPLOY_VENV_PATH`
- `STAGING_DEPLOY_SSH_KEY`
- `STAGING_PUBLIC_BASE_URL`
- `STAGING_ACCESS_KEY`

## Flow

1. изменения вливаются в `develop`
2. GitHub Actions запускает `.github/workflows/staging.yml`
3. `verify` прогоняет проверки
4. `deploy-staging` выкатывает текущий `develop`
5. staging используется для ручной проверки перед production release

Важно:
- staging frontend и staging backend теперь живут отдельно
- staging frontend выкатывается из frontend-репозитория, backend staging — из backend-репозитория

## Быстрая проверка

- `https://staging-api.wobbly.site/health`
- `https://staging-api.wobbly.site/ready`
- `https://staging-api.wobbly.site/api/swagger`
- `https://staging-api.wobbly.site/api/docs`
- `https://admin.wobbly.site/staging/`

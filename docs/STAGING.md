# Staging

Этот файл описывает staging-среду и должен считаться develop-only operational document.

Если документ попал в `main`, это ошибка release flow.

## Staging Baseline

- staging path: `/opt/rating-service-staging`
- staging service: `rating-service-staging.service`
- staging DB: `app_staging`
- staging port: `8001`
- staging public URL: `https://staging-api.wobbly.site`
- staging nginx protection: `X-Staging-Key`
- staging workflow: `.github/workflows/staging.yml`

## Staging Admin

- admin UI: `https://admin.wobbly.site/staging/`
- same-origin admin API:
  - `/staging/api/...`
- staging используется для ручной проверки UI/API до production release

## Staging Secrets

- `STAGING_DEPLOY_HOST`
- `STAGING_DEPLOY_USER`
- `STAGING_DEPLOY_PATH`
- `STAGING_DEPLOY_SERVICE`
- `STAGING_DEPLOY_OWNER`
- `STAGING_DEPLOY_VENV_PATH`
- `STAGING_DEPLOY_SSH_KEY`
- `STAGING_PUBLIC_BASE_URL`
- `STAGING_ACCESS_KEY`

## Staging Release Flow

1. feature branch вливается в `develop`
2. GitHub Actions запускает `.github/workflows/staging.yml`
3. `verify` прогоняет проверки
4. `deploy-staging` выкатывает текущий `develop` в staging
5. staging используется для проверки перед production release

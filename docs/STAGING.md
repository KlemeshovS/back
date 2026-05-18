# Staging

Этот файл существует только на ветке `develop` и удаляется при подготовке production release через `prepare_main_release.sh`.

## Staging topology

- путь: `/opt/rating-service-staging`
- сервис: `rating-service-staging.service`
- порт: `8001`
- venv: `/opt/rating-service-staging/.venv`
- публичный URL: `https://staging-api.wobbly.site`
- admin staging: `https://admin.wobbly.site/staging/`
- staging frontend bundle: `/opt/wobbly-front-staging/current`

## Доступ

Staging API защищён nginx — требует заголовок `X-Staging-Key`:

```bash
curl -H "X-Staging-Key: <значение из secret STAGING_ACCESS_KEY>" https://staging-api.wobbly.site/health
```

SSH на сервер:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

## GitHub Secrets для staging

| Secret | Значение |
|--------|----------|
| `STAGING_DEPLOY_HOST` | `api.wobbly.site` |
| `STAGING_DEPLOY_USER` | `root` |
| `STAGING_DEPLOY_PATH` | `/opt/rating-service-staging` |
| `STAGING_DEPLOY_SERVICE` | `rating-service-staging` |
| `STAGING_DEPLOY_OWNER` | `ratingapp:ratingapp` |
| `STAGING_DEPLOY_VENV_PATH` | `/opt/rating-service-staging/.venv` |
| `STAGING_DEPLOY_HEALTHCHECK_URL` | `http://127.0.0.1:8001/ready` |
| `STAGING_DEPLOY_SSH_KEY` | приватный SSH ключ |
| `STAGING_ACCESS_KEY` | ключ для заголовка `X-Staging-Key` |
| `STAGING_PUBLIC_BASE_URL` | `https://staging-api.wobbly.site` |

## CI/CD

`.github/workflows/staging.yml` запускается при каждом push в `develop`:
1. `verify` — format, lint, tests с реальной PostgreSQL
2. `deploy-staging` — деплой через `deploy_release.sh` с `STAGING_DEPLOY_*` секретами
3. smoke check `$STAGING_PUBLIC_BASE_URL/api/docs` и `/api/swagger` с `X-Staging-Key`

## Проверка

```bash
# health
curl -H "X-Staging-Key: <key>" https://staging-api.wobbly.site/health

# ready
curl -H "X-Staging-Key: <key>" https://staging-api.wobbly.site/ready

# swagger
curl -H "X-Staging-Key: <key>" https://staging-api.wobbly.site/api/swagger

# текущая версия на сервере
ssh root@api.wobbly.site 'cat /opt/rating-service-staging/.backend-release-version'
```

## Сервис

```bash
systemctl status rating-service-staging
systemctl restart rating-service-staging
journalctl -u rating-service-staging -n 100 --no-pager
```

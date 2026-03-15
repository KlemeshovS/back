# Deploy

## Read This First

Этот файл нужен для того, чтобы следующий чат или новый участник команды не тратил время на повторное расследование production-схемы.

Если задача связана с production, сначала опираемся на этот файл, и только потом идем проверять сервер.

## Current Production Topology

Текущий production работает не через docker compose и не через git checkout на сервере.

Реальная схема:
- `nginx`
- `rating-service.service`
- `uvicorn`
- код приложения лежит в `/opt/rating-service`

Это уже подтверждено на живом сервере.

Сетевые адреса:
- main site: `https://wobbly.site`
- API: `https://api.wobbly.site`
- Swagger: `https://api.wobbly.site/api/swagger`
- text docs: `https://api.wobbly.site/api/docs`

## Access

SSH-доступ:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

Рабочий пользователь для приложения:
- `ratingapp`

## What Not To Assume

Не надо автоматически предполагать:
- что production поднимается через `docker compose up`
- что на сервере лежит git checkout текущего репозитория
- что нужно делать `git pull` на сервере
- что live setup надо заново искать через полный обход `/etc`, `/opt`, `/srv` и systemd

Для текущего production это неверные стартовые предположения.

## Production Paths

Основной каталог приложения:

```text
/opt/rating-service
```

Ключевые пути:
- app code: `/opt/rating-service/app`
- backups created during manual deploys: `/opt/rating-service/.deploy-backups`

## Quick Verification Commands

Быстро проверить текущую продовую схему можно так:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'systemctl status rating-service --no-pager -l'
```

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'curl -fsS http://127.0.0.1:8000/health'
```

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'nginx -t'
```

## Services

Основной systemd unit:

```bash
systemctl status rating-service
```

Перезапуск:

```bash
systemctl restart rating-service
```

Проверка логов:

```bash
journalctl -u rating-service -n 100 --no-pager
```

## Nginx

Конфиги живут в:
- `/etc/nginx/sites-available/`
- `/etc/nginx/sites-enabled/`

Текущие домены обслуживаются через nginx:
- `api.wobbly.site`
- `wobbly.site`

Проверка конфига:

```bash
nginx -t
```

Перезагрузка:

```bash
systemctl reload nginx
```

## Certificates

Сертификаты выпускаются через `certbot --nginx`.

Текущие домены с HTTPS:
- `api.wobbly.site`
- `wobbly.site`

## Real Deploy Procedure

### Important

На сервере в `/opt/rating-service` лежит не git checkout, а рабочая копия проекта.

Поэтому нормальный ручной деплой здесь такой:
1. обновить нужные файлы через `scp`
2. выставить владельца `ratingapp:ratingapp`, если нужно
3. перезапустить `rating-service`
4. прогнать smoke-check

Если изменяются только статические файлы или шаблоны, этого достаточно. Если меняется Python-код, логика та же: копируем обновленные файлы в `/opt/rating-service`, затем перезапускаем `rating-service`.

### Example Deploy

```bash
scp -i /Users/klem/Documents/eguene/deploy_key /local/file root@api.wobbly.site:/opt/rating-service/path/to/file
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'chown ratingapp:ratingapp /opt/rating-service/path/to/file && systemctl restart rating-service'
```

### If multiple files changed

Можно копировать директории, например:

```bash
scp -i /Users/klem/Documents/eguene/deploy_key -r /Users/klem/Documents/eguene/app/static root@api.wobbly.site:/opt/rating-service/app/
```

## Recommended Safe Manual Deploy

Перед заменой файлов желательно сделать резервную копию:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'mkdir -p /opt/rating-service/.deploy-backups/DATE_TAG'
```

Потом скопировать старые файлы туда:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'cp /opt/rating-service/path/to/file /opt/rating-service/.deploy-backups/DATE_TAG/'
```

После копирования новых файлов:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'chown ratingapp:ratingapp /opt/rating-service/path/to/file && systemctl restart rating-service'
```

## Smoke Checks After Deploy

Проверка API локально на сервере:

```bash
curl -fsS http://127.0.0.1:8000/health
```

Проверка публичного API:

```bash
curl -I https://api.wobbly.site/api/swagger
curl -I https://api.wobbly.site/api/docs
curl -I https://api.wobbly.site/docs
```

Проверка главной страницы:

```bash
curl -I https://wobbly.site
```

Проверка локализации landing page:

```bash
curl -H 'Accept-Language: ru-RU,ru;q=0.9' https://wobbly.site
curl -H 'Accept-Language: en-US,en;q=0.9' https://wobbly.site
```

## Minimal Deploy Checklist

Если нужно быстро и без повторного исследования выкатить изменение:
1. локально проверить измененные файлы
2. при необходимости сделать backup в `/opt/rating-service/.deploy-backups/DATE_TAG`
3. скопировать файлы в `/opt/rating-service`
4. выставить владельца `ratingapp:ratingapp`
5. перезапустить `rating-service`
6. проверить `/health`
7. проверить затронутые публичные URL

## Handoff Summary

Если контекст переносится в новый чат, этот блок можно считать краткой operational truth:
- production code lives in `/opt/rating-service`
- service name is `rating-service.service`
- public reverse proxy is `nginx`
- SSH access uses `root@api.wobbly.site` and local `deploy_key`
- production deploy is manual file copy plus service restart
- `docker compose` в репозитории не является текущим live deploy path

## Notes For Future Chats

Если контекст переносится в новый чат, не надо заново угадывать прод-контур.

Нужно сразу опираться на эти факты:
- prod path: `/opt/rating-service`
- service: `rating-service.service`
- reverse proxy: `nginx`
- API host: `api.wobbly.site`
- site host: `wobbly.site`
- deploy access: `root@api.wobbly.site` через `deploy_key`
- prod deploy is file copy + systemctl restart, not git pull on server

## CI/CD Automation

Теперь стандартный целевой flow такой:
1. разработка идет в короткой ветке
2. ветка вливается в `main`
3. GitHub Actions запускает `.github/workflows/pipeline.yml`
4. job `verify` прогоняет проверки
5. если проверки успешны, job `deploy` выкатывает текущий `main` на production

### GitHub Secrets

Для workflow нужно завести такие secrets в GitHub repository settings:
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PATH`
- `DEPLOY_SERVICE`
- `DEPLOY_OWNER`
- `DEPLOY_SSH_KEY`

Для текущего production значения такие:
- `DEPLOY_HOST=api.wobbly.site`
- `DEPLOY_USER=root`
- `DEPLOY_PATH=/opt/rating-service`
- `DEPLOY_SERVICE=rating-service`
- `DEPLOY_OWNER=ratingapp:ratingapp`

`DEPLOY_SSH_KEY` должен содержать приватный ключ, который пускает на production-сервер.

### Workflow Behavior

`pipeline.yml` делает следующее:
- на `pull_request` в `main` запускает только `verify`
- на `push` в `main` запускает `verify`, а затем `deploy`

### Local Scripts Used By CI/CD

Pipeline опирается на два локальных скрипта:
- `scripts/ci_check.sh`
- `scripts/deploy_release.sh`

Это сделано специально, чтобы логика проверки и деплоя не была размазана только по YAML.

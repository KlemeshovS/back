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
- схема БД управляется через `Alembic`

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

## Source Of Truth For Docs Page

Человекочитаемая API docs page на `https://api.wobbly.site/api/docs` собирается клиентским JavaScript.

Файлы:
- `app/static/pages/api-docs.html`
- `app/static/css/api-docs.css`
- `app/static/js/api-docs.js`

Это важно для проверки:
- сырой `curl` по `/api/docs` покажет HTML-оболочку
- содержимое секций и endpoint descriptions живет в `app/static/js/api-docs.js`
- если нужно проверить, обновилась ли текстовая документация после API change, смотри и production URL, и `app/static/js/api-docs.js`

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

## Certificates

Сертификаты выпускаются через `certbot --nginx`.

Текущие домены с HTTPS:
- `api.wobbly.site`
- `wobbly.site`

## CI/CD Automation

Теперь стандартный flow такой:
1. разработка идет в короткой ветке
2. ветка вливается в `main`
3. GitHub Actions запускает `.github/workflows/pipeline.yml`
4. job `verify` прогоняет проверки
5. если проверки успешны, job `deploy` выкатывает текущий `main` на production

Текущее состояние:
- workflow уже лежит в репозитории: `.github/workflows/pipeline.yml`
- repository secrets для deploy уже заведены в GitHub
- целевой основной путь доставки теперь через GitHub Actions, а не через ручной `scp`

### Workflow Behavior

`pipeline.yml` делает следующее:
- на `pull_request` в `main` запускает только `verify`
- на `push` в `main` запускает `verify`, а затем `deploy`
- `verify` ставит Python и Node tooling, гоняет `ruff`, `pytest`, JS syntax checks, Docker config validation и docs sync check
- `verify` checkout'ит репозиторий с полной историей, чтобы docs sync check мог сравнивать `base sha` и `head sha`
- `deploy` собирает release archive, копирует его на production и перезапускает `rating-service`

### Database Migrations

Схема БД теперь управляется через `Alembic`.

Что важно:
- миграции лежат в `alembic/versions/`
- приложение на старте вызывает `alembic upgrade head` программно через `app/db/database.py`
- это дает плавный переход без отдельного ручного SQL на сервере

### GitHub Secrets

Для workflow нужны такие secrets в GitHub repository settings:
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_PATH`
- `DEPLOY_SERVICE`
- `DEPLOY_OWNER`
- `DEPLOY_VENV_PATH`
- `DEPLOY_SSH_KEY`

Для текущего production значения такие:
- `DEPLOY_HOST=api.wobbly.site`
- `DEPLOY_USER=root`
- `DEPLOY_PATH=/opt/rating-service`
- `DEPLOY_SERVICE=rating-service`
- `DEPLOY_OWNER=ratingapp:ratingapp`
- `DEPLOY_VENV_PATH=/opt/rating-service/.venv`

Если `DEPLOY_VENV_PATH` не задан, deploy script использует дефолт:
- `${DEPLOY_PATH}/.venv`

### Local Scripts Used By CI/CD

Pipeline опирается на локальные скрипты:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`

Во время deploy script теперь:
- распаковывает release
- обновляет Python dependencies в production venv через `pip install -r requirements.txt`
- только потом перезапускает `rating-service`

## API Docs Sync Rule

Если меняется API, pipeline должен увидеть обновление docs в том же изменении.

Проверка делается скриптом:
- `scripts/check_api_docs_sync.sh`

После рефакторинга ориентироваться нужно на текущую архитектуру:
- route and behavior changes обычно живут в `app/api/routes/`
- schema changes живут в `app/domain/`
- business logic живет в `app/services/`
- auth and shared behavior могут жить в `app/core/`

Если поведение API меняется, вместе с этим должны обновляться:
- `app/static/js/api-docs.js`
- при необходимости `MOBILE_API.md`
- при необходимости `README.md`

## Common Failure: SSH Key Parsing

Если GitHub Actions падает с ошибкой вида:

```text
Load key "/home/runner/.ssh/deploy_key": error in libcrypto
Permission denied (publickey,password)
```

Почти всегда это значит одно из следующего:
- в `DEPLOY_SSH_KEY` вставлен публичный ключ вместо приватного
- приватный ключ вставлен без переносов строк
- ключ поврежден при копировании
- ключ зашифрован passphrase и runner не может его открыть

Правильный `DEPLOY_SSH_KEY` должен выглядеть примерно так:

```text
-----BEGIN OPENSSH PRIVATE KEY-----
...
-----END OPENSSH PRIVATE KEY-----
```

Для этого проекта ориентир такой:
- локально этот же ключ должен пускать командой `ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site`
- именно содержимое этого приватного файла и нужно класть в `DEPLOY_SSH_KEY`

## Real Manual Deploy Procedure

### Important

На сервере в `/opt/rating-service` лежит не git checkout, а рабочая копия проекта.

Поэтому нормальный ручной deploy здесь такой:
1. обновить нужные файлы через `scp`
2. выставить владельца `ratingapp:ratingapp`, если нужно
3. перезапустить `rating-service`
4. прогнать smoke-check

### Example Deploy

```bash
scp -i /Users/klem/Documents/eguene/deploy_key /local/file root@api.wobbly.site:/opt/rating-service/path/to/file
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

## Handoff Summary

Если контекст переносится в новый чат, этот блок можно считать краткой operational truth:
- production code lives in `/opt/rating-service`
- service name is `rating-service.service`
- public reverse proxy is `nginx`
- SSH access uses `root@api.wobbly.site` and local `deploy_key`
- primary production deploy is GitHub Actions after merge to `main`
- manual production deploy is fallback file copy plus service restart
- `docker compose` в репозитории не является текущим live deploy path

## Operational Rule

Если pipeline зеленый после merge в `main`, это и есть основной подтвержденный deploy result.

К ручному деплою стоит возвращаться только если:
- GitHub Actions недоступен
- сломан deploy job
- нужен срочный hotfix вне обычного flow

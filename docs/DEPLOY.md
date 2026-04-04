# Deploy

## Read This First

Этот файл нужен для того, чтобы следующий чат или новый участник команды не тратил время на повторное расследование production-схемы.

Если задача связана с production, сначала опираемся на этот файл, и только потом идем проверять сервер.

Этот документ описывает production-only truth.

Если задача про staging, нужно читать `docs/STAGING.md` на ветке `develop`.

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

Этот документ production-only.

Staging operational details должны жить только в `docs/STAGING.md` на ветке `develop`.

Admin baseline:
- admin public URL: `https://admin.wobbly.site`
- admin UI paths:
  - `/production/`
- `admin.wobbly.site/production/` использует production UI shell с `127.0.0.1:8000`
- admin same-origin API:
  - `/production/api/...` -> production `/admin/...`
- admin frontend assets теперь идут через:
  - `/assets/...`
  - `/og/...`
- admin certificate уже выпущен через `certbot --nginx`
- owner bootstrap уже применен через env на production
- bootstrap credentials это operational secret и не хранятся в репозитории
- production docs and checks should describe only production-facing behavior

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
- app code: `/opt/rating-service/backend/app`
- backups created during manual deploys: `/opt/rating-service/.deploy-backups`

## Source Of Truth For Docs Page

Человекочитаемая API docs page на `https://api.wobbly.site/api/docs` собирается клиентским JavaScript.

Файлы:
- `frontend/src/pages/ApiDocsPage.vue`
- `frontend/src/features/docs/content.ts`
- build output в `backend/app/static/`

Это важно для проверки:
- сырой `curl` по `/api/docs` покажет HTML-оболочку
- содержимое секций и endpoint descriptions живет в `frontend/src/features/docs/content.ts`
- если нужно проверить, обновилась ли текстовая документация после API change, смотри и production URL, и `frontend/src/features/docs/content.ts`
- docs page должна грузить assets через `/assets/...`
- если `/api/docs` белая, сначала проверить 404 на frontend bundle, а не backend routes

## Quick Verification Commands

Быстро проверить текущую продовую схему можно так:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'systemctl status rating-service --no-pager -l'
```

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'curl -fsS http://127.0.0.1:8000/health'
```

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'curl -fsS http://127.0.0.1:8000/ready'
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

Для `api.wobbly.site` rate limiting config теперь хранится в репозитории:
- `deploy/nginx/api-rate-limits.conf`
- `deploy/nginx/api.wobbly.site.conf`
- production templates в репозитории:
  - `deploy/systemd/rating-service.service`

Текущий production уже использует этот rate limiting слой:
- `10 requests/second` на IP
- burst `30`
- `20` одновременных соединений на IP

## Certificates

Сертификаты выпускаются через `certbot --nginx`.

Текущие домены с HTTPS:
- `api.wobbly.site`
- `wobbly.site`

## CI/CD Automation

Теперь стандартный flow такой:
1. разработка идет в короткой ветке
2. ветка вливается в `develop`
3. staging verify/deploy живет только в `develop`
4. когда пользователь явно запрашивает production release, выбирается новая backend version в `backend/VERSION`
5. из `develop` готовится отдельная release-ветка через `scripts/prepare_main_release.sh codex/release-main <backend-version>`
6. в release-ветке убираются staging-only workflow/templates/docs
7. release-ветка вливается в `main`
8. GitHub Actions запускает `.github/workflows/pipeline.yml`
9. pipeline создает tag `backend/v<version>`
10. job `deploy` выкатывает текущий `main` на production

Текущее состояние:
- workflow уже лежит в репозитории: `.github/workflows/pipeline.yml`
- manual backend deploy / rollback workflow лежит в репозитории: `.github/workflows/deploy-backend-release.yml`
- UI-friendly rollback workflow лежит в репозитории: `.github/workflows/rollback-backend-release.yml`
- production pipeline также создает GitHub Release `Backend v<version>`
- repository secrets для deploy уже заведены в GitHub
- целевой основной путь доставки теперь через GitHub Actions, а не через ручной `scp`

Важно:
- production release не делается прямым merge `develop -> main`
- staging operational artifacts не должны попадать в `main`

### Workflow Behavior

`pipeline.yml` делает следующее:
- на `pull_request` в `main` запускает только `verify`
- на `push` в `main` запускает `verify`, а затем `deploy`
- перед deploy читает `backend/VERSION` и создает tag `backend/v<version>`, если его еще нет
- затем создает или обновляет GitHub Release для этого tag
- `verify` ставит Python и Node tooling, гоняет backend checks, frontend lint/build, Docker config validation и docs sync check
- `verify` checkout'ит репозиторий с полной историей, чтобы docs sync check мог сравнивать `base sha` и `head sha`
- `deploy` собирает release archive, копирует его на production и перезапускает `rating-service`

`deploy-backend-release.yml` делает следующее:
- запускается вручную через `workflow_dispatch`
- принимает `git_ref` вида `backend/v0.1.0` или commit SHA
- checkout'ит именно этот ref
- выкатывает выбранную backend version на production
- подходит для rollback и ручной установки конкретной backend версии

`rollback-backend-release.yml` делает следующее:
- запускается вручную через `workflow_dispatch`
- принимает только release tag вида `backend/v0.1.0`
- предназначен именно для простого rollback через GitHub UI
- после выполнения пишет summary с восстановленной backend version

### Database Migrations

Схема БД теперь управляется через `Alembic`.

Что важно:
- миграции лежат в `backend/alembic/versions/`
- приложение на старте вызывает `alembic upgrade head` программно через `backend/app/db/database.py`
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

`pipeline.yml` production deploy gate:
- `http://127.0.0.1:8000/ready`

## Production Quick Checklist

После production release быстро проверить:
- `https://api.wobbly.site/health`
- `https://api.wobbly.site/ready`
- `https://api.wobbly.site/api/swagger`
- `https://api.wobbly.site/api/docs`
- `https://wobbly.site`
- `https://admin.wobbly.site/production/`

### Current Backend Release Metadata

На production текущую backend version можно посмотреть так:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'cat /opt/rating-service/.backend-release-version'
```

Текущий production tag:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'cat /opt/rating-service/.backend-release-tag'
```

Текущий production commit ref:

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site 'cat /opt/rating-service/.backend-release-ref'
```

### Rollback Backend Release

Если нужно откатить backend:
1. открыть GitHub Actions
2. для обычного rollback выбрать workflow `Rollback Backend Release`
3. передать `release_tag`

Если нужен deploy не по tag, а по произвольному ref:
1. открыть GitHub Actions
2. выбрать workflow `Deploy Backend Release`
3. передать `git_ref`

Допустимые значения `release_tag`:
- `backend/v0.1.0`
- `backend/v0.2.0`

Допустимые значения `git_ref`:
- `backend/v0.1.0`
- `backend/v0.2.0`
- конкретный commit SHA

Предпочтительный rollback path:
- сначала использовать workflow `Rollback Backend Release` с release tag `backend/v...`
- commit SHA использовать только если tag еще не заведен или нужен точечный hotfix rollback

Все staging secrets и staging deploy значения intentionally documented only in `docs/STAGING.md` on `develop`.

### Local Scripts Used By CI/CD

Pipeline опирается на локальные скрипты:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`
- `scripts/read_backend_version.sh`

Systemd templates в репозитории:
- `deploy/systemd/rating-service.service`

Во время deploy script теперь:
- распаковывает release
- обновляет Python dependencies в production venv через `pip install -r backend/requirements.txt`
- сохраняет immutable backend archive в `/opt/rating-service/.releases/`
- пишет metadata текущего backend deploy в:
  - `/opt/rating-service/.backend-release-version`
  - `/opt/rating-service/.backend-release-ref`
  - `/opt/rating-service/.backend-release-tag`
- только потом перезапускает `rating-service`
- ждет не только `systemctl is-active`, но и успешный ответ healthcheck URL
- если `/ready` не поднимается вовремя, печатает свежие `journalctl` логи сервиса и завершает deploy с ошибкой
- не включает в release archive локальные dev-артефакты вроде `.venv`, caches и `frontend/node_modules`
- использует `/ready` как реальную пост-рестарт проверку доступности БД, а `/health` оставляет lightweight liveness endpoint

Важно:
- `nginx` конфиги не раскатываются текущим GitHub Actions deploy автоматически
- изменения в `deploy/nginx/` нужно применять на сервер отдельно через `nginx -t` и `systemctl reload nginx`
- admin host routing на `admin.wobbly.site` тоже не раскатывается автоматически через pipeline и остается отдельной server-side обязанностью

## API Docs Sync Rule

Если меняется API, pipeline должен увидеть обновление docs в том же изменении.

Проверка делается скриптом:
- `scripts/check_api_docs_sync.sh`

После рефакторинга ориентироваться нужно на текущую архитектуру:
- route and behavior changes обычно живут в `backend/app/api/routes/`
- schema changes живут в `backend/app/domain/`
- business logic живет в `backend/app/services/`
- auth and shared behavior могут жить в `backend/app/core/`

Если поведение API меняется, вместе с этим должны обновляться:
- `frontend/src/features/docs/content.ts`
- при необходимости `docs/MOBILE_API.md`
- при необходимости `README.md`

### Admin Smoke Checks

После frontend/backend split smoke checks должны проверять не только API и landing, но и admin surface:
- `https://admin.wobbly.site/production/`

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

```bash
curl -fsS http://127.0.0.1:8000/ready
```

Проверка публичного API:

```bash
curl -I https://api.wobbly.site/api/swagger
curl -I https://api.wobbly.site/api/docs
curl -I https://api.wobbly.site/docs
```

Важно:
- health/readiness для release gate сейчас проверяются локально на сервере через `127.0.0.1`
- внешний post-deploy smoke-check должен проверять публичные user-facing surfaces, а не внутреннюю готовность процесса
- nginx конфиги не раскатываются автоматически вместе с кодом, поэтому внешний `/health` или `/ready` не стоит делать обязательным pipeline gate без отдельной синхронизации server nginx

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

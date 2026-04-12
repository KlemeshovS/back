# Deploy

## Read This First

Этот файл нужен для того, чтобы следующий участник команды не тратил время на повторное расследование production-схемы.

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
- production frontend лежит в `/opt/wobbly-front-production/current`
- staging frontend лежит в `/opt/wobbly-front-staging/current`
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
- `admin.wobbly.site/production/` должен обслуживаться отдельным production frontend bundle
- `admin.wobbly.site/staging/` должен обслуживаться отдельным staging frontend bundle
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
- automated PostgreSQL backups: `/var/backups/wobbly-postgres`
- uploaded user avatars by default: `/opt/rating-service/uploads/avatars`
- production frontend bundle: `/opt/wobbly-front-production/current`
- staging backend: `/opt/rating-service-staging`
- staging frontend bundle: `/opt/wobbly-front-staging/current`

## Automated Backups

Production backup flow now lives in the repository:
- script: `scripts/backup_postgres.sh`
- systemd unit: `deploy/systemd/wobbly-postgres-backup.service`
- systemd timer: `deploy/systemd/wobbly-postgres-backup.timer`
- env template: `deploy/backup.env.example`

What it does:
- runs a daily `pg_dump`
- stores local backups in `/var/backups/wobbly-postgres/daily`
- keeps only the last `LOCAL_RETENTION_DAYS` of local copies
- updates `latest.dump` and `latest.sha256`
- can copy each backup off-server through `rclone`

### Server Setup

1. Copy the env template:

```bash
mkdir -p /etc/wobbly
cp /opt/rating-service/deploy/backup.env.example /etc/wobbly/backup.env
```

2. Edit `/etc/wobbly/backup.env`:
- set `DATABASE_URL` or `PG*`
- set `LOCAL_RETENTION_DAYS`
- set `RCLONE_REMOTE` and `RCLONE_DESTINATION`

3. Install `rclone` on the server and configure the remote:

```bash
apt-get update
apt-get install -y rclone
rclone config
```

4. Install the systemd files:

```bash
cp /opt/rating-service/deploy/systemd/wobbly-postgres-backup.service /etc/systemd/system/
cp /opt/rating-service/deploy/systemd/wobbly-postgres-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now wobbly-postgres-backup.timer
```

### Verification

Run one backup manually:

```bash
systemctl start wobbly-postgres-backup.service
```

Check timer state:

```bash
systemctl status wobbly-postgres-backup.timer
systemctl list-timers --all | grep wobbly-postgres-backup
```

Check backup output:

```bash
ls -lah /var/backups/wobbly-postgres/daily
journalctl -u wobbly-postgres-backup.service -n 50 --no-pager
```

## Uptime Monitoring

Стартовый automated uptime monitoring для production разворачивается через `Uptime Kuma`.

Файлы в репозитории:
- compose: `deploy/monitoring/uptime-kuma.compose.yml`
- env template: `deploy/monitoring/uptime-kuma.env.example`
- install helper: `scripts/install_uptime_kuma.sh`
- setup doc: `docs/UPTIME_MONITORING.md`

### Server Setup

На production server:

```bash
cd /opt/rating-service
bash scripts/install_uptime_kuma.sh
```

Что делает install helper:
- создает `/opt/uptime-kuma`
- создает `/opt/uptime-kuma/data`
- копирует `.env` из шаблона, если файла еще нет
- поднимает контейнер `uptime-kuma`

### Access

По умолчанию Uptime Kuma слушает только localhost:

```text
http://127.0.0.1:3001
```

Безопасный доступ:

```bash
ssh -L 3001:127.0.0.1:3001 -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

После этого локально открыть:

```text
http://127.0.0.1:3001
```

### Initial Monitors

Создать в UI:
- `API Health` -> `https://api.wobbly.site/health`
- `Main Site` -> `https://wobbly.site`

Добавить позже как отдельный readiness monitor:
- `API Ready` -> `https://api.wobbly.site/ready`

### Verification

Проверить контейнер и логи:

```bash
docker ps --filter name=uptime-kuma
docker logs --tail=100 uptime-kuma
```

## Telegram Status Bot

Если нужен ручной запрос статуса через Telegram-команду `/status`, в production можно поднять отдельный polling-бот.

Файлы в репозитории:
- env template: `deploy/telegram-status-bot.env.example`
- systemd unit: `deploy/systemd/wobbly-telegram-status-bot.service`
- script: `scripts/telegram_status_bot.py`

### Server Setup

```bash
mkdir -p /etc/wobbly
cp /opt/rating-service/deploy/telegram-status-bot.env.example /etc/wobbly/telegram-status-bot.env
nano /etc/wobbly/telegram-status-bot.env
cp /opt/rating-service/deploy/systemd/wobbly-telegram-status-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now wobbly-telegram-status-bot.service
```

`telegram-status-bot.env` должен содержать:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_STATUS_ALLOWED_CHAT_ID`

Start version checks:
- `https://api.wobbly.site/health`
- `https://api.wobbly.site/ready`

### Verification

```bash
systemctl status wobbly-telegram-status-bot.service --no-pager
journalctl -u wobbly-telegram-status-bot.service -n 50 --no-pager
```

## User Avatar Storage

User avatars are stored outside the repository and outside frontend assets.

Relevant env settings:

```env
MEDIA_ROOT=/opt/rating-service/uploads
MEDIA_BASE_URL=https://api.wobbly.site
AVATAR_MAX_BYTES=5242880
```

Public URL shape:

```text
https://api.wobbly.site/media/avatars/<generated-file>
```

Notes:
- backend stores only relative `avatar_path` in the database
- `/media/...` is served by FastAPI from `MEDIA_ROOT`
- avatar uploads support `jpeg`, `png`, and `webp`

## Temporary Guest Rating Compatibility

Если iOS временно должен остаться на legacy guest flow, а Android уже использует новый auth flow, можно включить:

```env
ALLOW_GUEST_RATING=true
```

Эффект:
- guest может сохранять `username`
- guest может включать участие в рейтинге
- guest может отправлять `score`

По умолчанию:
- `ALLOW_GUEST_RATING=false`
- рейтинговый контур остается только для authenticated-пользователей

## Source Of Truth For Docs Page

Человекочитаемая API docs page на `https://api.wobbly.site/api/docs` собирается клиентским JavaScript.

Файлы:
- frontend repo: [Wobbly-develop/front](https://github.com/Wobbly-develop/front)
- `src/pages/ApiDocsPage.vue`
- `src/features/docs/content.ts`
- production build output должен выкладываться в отдельный frontend deploy dir и раздаваться nginx

Это важно для проверки:
- сырой `curl` по `/api/docs` покажет HTML-оболочку
- содержимое секций и endpoint descriptions живет в frontend-репозитории, в `src/features/docs/content.ts`
- если нужно проверить, обновилась ли текстовая документация после API change, смотри и production URL, и frontend repo `src/features/docs/content.ts`
- docs page должна грузить assets через `/assets/...`
- если `/api/docs` белая, сначала проверить 404 на frontend bundle, а не backend routes
- если браузер продолжает показывать старый HTML или `Welcome to nginx!`, сначала сделать hard reload или открыть страницу в incognito: после разделения front/back браузер может держать старую SPA-оболочку в disk cache

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
- `admin.wobbly.site`

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
5. из `develop` готовится отдельная release-ветка через `scripts/prepare_main_release.sh <release-branch> <backend-version>`
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
- release notes собираются из commit history между backend release tags через `scripts/generate_backend_release_notes.sh`
- `verify` работает только с backend-кодом и не зависит от frontend source
- `verify` checkout'ит репозиторий с полной историей, чтобы docs sync check мог сравнивать `base sha` и `head sha`
- `deploy` собирает release archive, копирует его на production и перезапускает `rating-service`
- `deploy` выкатывает только backend-код; frontend выкатывается отдельным workflow из frontend-репозитория

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
- `backend/v0.2.0-r1`

Допустимые значения `git_ref`:
- `backend/v0.1.0`
- `backend/v0.2.0`
- `backend/v0.2.0-r1`
- конкретный commit SHA

Предпочтительный rollback path:
- сначала использовать workflow `Rollback Backend Release` с release tag `backend/v...`
- commit SHA использовать только если tag еще не заведен или нужен точечный hotfix rollback

Если `backend/VERSION` не был увеличен, production pipeline больше не падает на конфликте tags:
- сначала он пытается использовать `backend/v<version>`
- если этот tag уже указывает на другой commit, pipeline автоматически создает следующий свободный tag вида `backend/v<version>-r1`, `backend/v<version>-r2` и так далее

Все staging secrets и staging deploy значения intentionally documented only in `docs/STAGING.md` on `develop`.

### Local Scripts Used By CI/CD

Pipeline опирается на локальные скрипты:
- `scripts/ci_check.sh`
- `scripts/check_api_docs_sync.sh`
- `scripts/deploy_release.sh`
- `scripts/generate_backend_release_notes.sh`
- `scripts/read_backend_version.sh`

Systemd templates в репозитории:
- `deploy/systemd/rating-service.service`

Во время deploy script теперь:
- распаковывает release
- определяет effective Python venv по `systemd ExecStart` текущего сервиса и только потом обновляет dependencies через `pip install -r backend/requirements.txt`
- если нужный venv отсутствует, создает его через `python3 -m venv`
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

Это важно:
- ошибочный `DEPLOY_VENV_PATH` или `STAGING_DEPLOY_VENV_PATH` secret больше не должен ломать deploy сам по себе
- если secret устарел, deploy script все равно берет venv из реального systemd unit, который запускает сервис

Важно:
- `nginx` конфиги не раскатываются текущим GitHub Actions deploy автоматически
- изменения в `deploy/nginx/` нужно применять на сервер отдельно через `nginx -t` и `systemctl reload nginx`
- admin host routing на `admin.wobbly.site` тоже не раскатывается автоматически через pipeline и остается отдельной server-side обязанностью
- live production сейчас уже переключен на независимую схему frontend/backend; репозиторий должен оставаться с ней синхронен

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
- frontend repo: `src/features/docs/content.ts`
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

Этот блок можно считать краткой operational truth:
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

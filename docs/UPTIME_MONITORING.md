# Uptime Monitoring

Стартовое решение для автоматического контроля доступности — `Uptime Kuma`.

Официальные источники:
- [Uptime Kuma GitHub README](https://github.com/louislam/uptime-kuma)
- [How to Update](https://github.com/louislam/uptime-kuma/wiki/%F0%9F%86%99-How-to-Update)
- [Notification Methods](https://github.com/louislam/uptime-kuma/wiki/Notification-Methods)

## Что мониторим

Сразу:
- `https://api.wobbly.site/health`
- `https://wobbly.site`

Чуть позже, когда хотим отдельный readiness alert:
- `https://api.wobbly.site/ready`

## Почему Uptime Kuma

- быстро поднимается в Docker
- удобный UI
- есть уведомления в Telegram, Email, Discord, Slack и многие другие каналы
- достаточно для стартового operational monitoring

## Установка на production server

На сервере из каталога backend deploy:

```bash
cd /opt/rating-service
bash scripts/install_uptime_kuma.sh
```

Скрипт:
- создаст `/opt/uptime-kuma`
- положит `.env` из шаблона
- поднимет контейнер `uptime-kuma`

Compose source в репозитории:
- `deploy/monitoring/uptime-kuma.compose.yml`

Env template:
- `deploy/monitoring/uptime-kuma.env.example`

## Где лежат данные

По умолчанию:

```text
/opt/uptime-kuma/data
```

Это важно:
- Uptime Kuma не должен хранить данные на NFS
- лучше использовать локальный диск/volume

## Как зайти в UI

По умолчанию контейнер слушает только localhost:

```text
http://127.0.0.1:3001
```

Безопасный способ зайти:

```bash
ssh -L 3001:127.0.0.1:3001 -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

Потом открыть локально:

```text
http://127.0.0.1:3001
```

Это лучше, чем сразу публиковать Uptime Kuma наружу.

## Какие мониторы создать

### 1. API Health

- Type: `HTTP(s)`
- Name: `API Health`
- URL: `https://api.wobbly.site/health`
- Interval: `60 seconds`
- Method: `GET`
- Accepted Status Codes: `200-299`

### 2. Main Site

- Type: `HTTP(s)`
- Name: `Main Site`
- URL: `https://wobbly.site`
- Interval: `60 seconds`
- Method: `GET`
- Accepted Status Codes: `200-299`

### 3. API Ready

Добавить позже как отдельный monitor:

- Type: `HTTP(s)`
- Name: `API Ready`
- URL: `https://api.wobbly.site/ready`
- Interval: `60 seconds`
- Method: `GET`
- Accepted Status Codes: `200-299`

## Уведомления

В Uptime Kuma UI нужно настроить хотя бы один notification channel.

Стартово рекомендовано одно из:
- Telegram
- Email (SMTP)
- Discord
- Slack

Рекомендация:
- сначала включить уведомления на `API Health` и `Main Site`
- потом добавить `API Ready`

## Проверка после запуска

Проверить контейнер:

```bash
docker ps --filter name=uptime-kuma
```

Проверить логи:

```bash
docker logs --tail=100 uptime-kuma
```

Проверить обновление:

```bash
docker compose --env-file /opt/uptime-kuma/.env -f deploy/monitoring/uptime-kuma.compose.yml pull
docker compose --env-file /opt/uptime-kuma/.env -f deploy/monitoring/uptime-kuma.compose.yml up -d --force-recreate
```

## Минимальный operational result

После настройки:
- API health будет проверяться автоматически
- main site будет проверяться автоматически
- о падении будет приходить уведомление
- отпадет необходимость ручных `curl`-проверок как основного способа контроля

## Telegram Status Bot

Если команде нужен ручной запрос статуса через Telegram-команду `/status`, рядом с Uptime Kuma можно поднять маленький polling-бот.

Что умеет стартовая версия:
- принимает `/status`
- проверяет:
  - `https://api.wobbly.site/health`
  - `https://api.wobbly.site/ready`
- отвечает статусом в Telegram-группу

Файлы:
- bot script: `scripts/telegram_status_bot.py`
- env template: `deploy/telegram-status-bot.env.example`
- systemd unit: `deploy/systemd/wobbly-telegram-status-bot.service`

### Server Setup

1. Скопировать env:

```bash
mkdir -p /etc/wobbly
cp /opt/rating-service/deploy/telegram-status-bot.env.example /etc/wobbly/telegram-status-bot.env
```

2. Отредактировать `/etc/wobbly/telegram-status-bot.env`:
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_STATUS_ALLOWED_CHAT_ID`
- `TELEGRAM_STATUS_TIMEZONE` (по умолчанию `Europe/Moscow`)
- при необходимости `STATUS_API_HEALTH_URL` и `STATUS_API_READY_URL`
- при необходимости `TELEGRAM_STATUS_POLL_TIMEOUT` для более быстрого ответа бота

3. Установить systemd unit:

```bash
cp /opt/rating-service/deploy/systemd/wobbly-telegram-status-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now wobbly-telegram-status-bot.service
```

### Verification

Проверить сервис:

```bash
systemctl status wobbly-telegram-status-bot.service --no-pager
journalctl -u wobbly-telegram-status-bot.service -n 50 --no-pager
```

После этого в разрешенной Telegram-группе команда:

```text
/status
```

должна вернуть краткий статус `health` и `ready` с отметкой времени в настроенном часовом поясе.

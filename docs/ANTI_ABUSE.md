# Anti-Abuse Plan

Этот документ отвечает на вопрос: как не дать внешним клиентам безнаказанно "долбиться" в API.

Важно:
- абсолютной защиты одним флагом не бывает
- защита строится слоями
- лучше отсекать мусор как можно раньше: сначала edge/reverse proxy, потом backend, потом product-level anti-fraud

## Current Baseline

Уже сделано:
- write-методы работают через bearer token
- есть rate limiting на создание anonymous user
- есть rate limiting на обновление score
- есть единый error contract
- включен `TrustedHostMiddleware`
- включен ограниченный CORS policy

Это уже защищает от части случайного мусора, но не заменяет сетевую защиту и антифрод.

## Recommended Defense Layers

### 1. Reverse Proxy Rate Limiting

Что сделать:
- добавить rate limiting на уровне `nginx`
- отдельно ограничить:
  - burst по IP
  - sustained rate по IP
  - количество одновременных соединений

Почему это важно:
- мусор лучше отбрасывать до Python
- это дешевле по CPU и памяти

Рекомендуемый приоритет:
- самый ближайший инфраструктурный шаг

### 2. Separate Limits Per Endpoint

Что сделать:
- оставить разные лимиты для разных endpoint'ов
- сделать `/auth/anonymous` самым жестким
- отдельно ужесточить `/me/score`
- при необходимости добавить отдельный лимит на `/me/profile`

Почему это важно:
- разные методы имеют разную стоимость и разный abuse profile

### 3. Token + IP Based Signals

Что сделать:
- логировать частоту запросов не только по IP, но и по token
- уметь видеть:
  - много токенов с одного IP
  - много score updates с одного token
  - странные скачки score

Почему это важно:
- один только IP rate limit не покрывает все сценарии abuse

### 4. Fail2ban or Similar IP Bans

Что сделать:
- банить IP, которые системно бьют в `401`, `429` или спамят endpoint'ы
- вводить временный ban, а не вечную блокировку

Почему это важно:
- это простой следующий слой после `nginx`

### 5. Cloudflare in Front of API

Что сделать:
- поставить `api.wobbly.site` за Cloudflare
- включить:
  - basic WAF
  - bot filtering
  - edge rate limiting

Почему это важно:
- часть мусора лучше резать еще до сервера
- это особенно полезно против более широкого внешнего шума

### 6. Product-Level Anti-Fraud

Что сделать:
- логировать резкие и неестественные изменения `score`
- анализировать поведение:
  - слишком частые обновления
  - аномально большие прыжки
  - одинаковые паттерны с одного IP/device

Почему это важно:
- даже нормальный auth не спасает от накрутки продукта, если пользователь авторизован, но ведет себя аномально

## First Practical Implementation

Что уже начали делать в коде:
- `TrustedHostMiddleware`
- ограниченный CORS

Почему это был первый шаг:
- не ломает мобильное приложение
- дешево внедряется
- сразу сокращает часть лишнего трафика и неправильных запросов

## First Infrastructure Layer

Следующий практический слой:
- `nginx` rate limiting для `api.wobbly.site`

Что добавлено в репозиторий:
- `deploy/nginx/api-rate-limits.conf`
- `deploy/nginx/api.wobbly.site.conf`

Что делает этот слой:
- ограничивает request rate по IP
- ограничивает количество одновременных соединений по IP
- возвращает `429`, если лимит превышен

Текущие значения:
- `10 requests/second` на IP
- burst `30`
- `20` одновременных соединений на IP

Это специально настроено мягко, чтобы:
- не мешать нормальной мобильной интеграции
- не резать Swagger и docs page
- при этом отсеивать простые burst-атаки и шум

## Recommended Execution Order

### Phase 1
- `TrustedHostMiddleware` and restrictive CORS
- nginx rate limiting
- tighter endpoint rate limits

### Phase 2
- structured logging
- request correlation
- fail2ban

### Phase 3
- Cloudflare
- anomaly detection on score updates
- anti-fraud markers

## Recommended Next Task

Если брать следующий самый полезный шаг после текущих backend-изменений:

`Add nginx rate limiting for api.wobbly.site`

Это самый практичный следующий слой, потому что он отсечет часть мусора еще до FastAPI.

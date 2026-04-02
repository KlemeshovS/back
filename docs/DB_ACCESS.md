# DB Access

Этот файл нужен для быстрого доступа к PostgreSQL в двух средах:
- production
- staging

Важно:
- этот документ нужен в первую очередь на `develop`, потому что включает staging operational context
- если задача касается production-only release knowledge, сначала читать `docs/DEPLOY.md`

Ниже есть два способа:
- через терминал (`ssh` + `psql`)
- через GUI (`DBeaver`)

## Environments

### Production
- SSH host: `api.wobbly.site`
- DB name: `app`
- app path: `/opt/rating-service`

### Staging
- SSH host: `api.wobbly.site`
- DB name: `app_staging`
- app path: `/opt/rating-service-staging`

Важно:
- PostgreSQL наружу не открыт
- для GUI лучше использовать `SSH tunnel`
- для production и staging сервер один и тот же, но базы разные

## Terminal Access

### 1. Подключиться к серверу

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

### 2. Зайти в production DB

```bash
sudo -u postgres psql -d app
```

### 3. Зайти в staging DB

```bash
sudo -u postgres psql -d app_staging
```

### 4. Полезные команды внутри `psql`

Посмотреть пользователей:

```sql
SELECT id, username, score
FROM users
ORDER BY id;
```

Удалить пользователя:

```sql
DELETE FROM users
WHERE username = 'kostya';
```

Посмотреть конкретного пользователя:

```sql
SELECT *
FROM users
WHERE username = 'kostya';
```

Выйти:

```sql
\q
```

## One-Liners Without Interactive psql

### Production

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site "sudo -u postgres psql -d app -c \"SELECT id, username, score FROM users ORDER BY id;\""
```

### Staging

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site "sudo -u postgres psql -d app_staging -c \"SELECT id, username, score FROM users ORDER BY id;\""
```

## DBeaver Access

Лучший способ — через `SSH tunnel`.

### 1. Поднять tunnel для production

Открой отдельный терминал:

```bash
ssh -L 5433:127.0.0.1:5432 -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

Пока это окно открыто, production DB доступна локально на:
- host: `127.0.0.1`
- port: `5433`

### 2. Поднять tunnel для staging

В отдельном окне:

```bash
ssh -L 5434:127.0.0.1:5432 -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
```

Пока это окно открыто, staging DB доступна локально на:
- host: `127.0.0.1`
- port: `5434`

Важно:
- production и staging идут в один и тот же локальный PostgreSQL на сервере
- различие будет не в порту сервера, а в имени базы в DBeaver:
  - `app`
  - `app_staging`

Можно и production, и staging открывать через один tunnel на `5433`; главное не перепутать database name.
Отдельные локальные порты даны просто для удобства.

## DBeaver Settings

### Production
- Host: `127.0.0.1`
- Port: `5433`
- Database: `app`
- Username: `app`
- Password: пароль из `/opt/rating-service/.env`

### Staging
- Host: `127.0.0.1`
- Port: `5434`
- Database: `app_staging`
- Username: `app_staging`
- Password: пароль из `/opt/rating-service-staging/.env`

## How To Find DB Credentials

### Production

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
cat /opt/rating-service/.env
```

### Staging

```bash
ssh -i /Users/klem/Documents/eguene/deploy_key root@api.wobbly.site
cat /opt/rating-service-staging/.env
```

Ищи:

```env
DATABASE_URL=postgresql://user:password@127.0.0.1:5432/dbname
```

## Safety Rule

Перед `DELETE` или `UPDATE` сначала делай `SELECT`.

Правильный порядок:

```sql
SELECT *
FROM users
WHERE username = 'kostya';
```

Потом:

```sql
DELETE FROM users
WHERE username = 'kostya';
```

## Recommended Use

Если нужно быстро посмотреть и поправить данные:
- `ssh` + `psql`

Если нужно удобно фильтровать, смотреть таблицы и вручную редактировать:
- `DBeaver` + `SSH tunnel`

## Safety Reminder

Для production:
- сначала `SELECT`
- потом только `UPDATE` или `DELETE`
- если правка нужна не для срочного инцидента, лучше сначала зафиксировать ее как задачу или migration, а не делать ad-hoc change в БД

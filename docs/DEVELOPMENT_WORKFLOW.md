# Development Workflow

Правила работы для backend-репозитория.

## Ветки

- `develop` — основная ветка разработки
- `main` — production-only ветка
- задачи делаются в коротких ветках от `develop`
- прямой `develop -> main` не используем
- любые обычные изменения ведутся через `develop`
- в `main` пушим только по прямой просьбе владельца
- любой push в `main` считается релизом

## Именование веток

Используем префиксы:
- `feat/`
- `fix/`
- `docs/`
- `refactor/`
- `test/`
- `chore/`

## Коммиты

Используем `Conventional Commits`.

Примеры:
- `feat(api): add readiness endpoint`
- `fix(users): reject clearing username`
- `docs(repo): update backend docs`

## Обычная разработка

1. создать ветку от `develop`
2. поднять локальную БД и API
3. внести изменения
4. прогнать `./scripts/ci_check.sh`
5. сделать commit
6. push в свою ветку
7. влить в `develop`
8. дождаться staging pipeline

## Production release

1. убедиться, что `develop` зеленый
2. обязательно прогнать релизную проверку без skip:

```bash
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./scripts/release_check.sh
```

Если релизная проверка не прошла полностью, merge или push в `main` запрещен.

3. обновить `backend/VERSION`
4. подготовить release branch через `scripts/prepare_main_release.sh`
5. влить release branch в `main`
6. дождаться production pipeline

## Проверки и hooks

Основная команда:

```bash
./scripts/ci_check.sh
```

Отдельная команда именно для релиза:

```bash
TEST_DATABASE_URL=postgresql://app:app@127.0.0.1:5432/app ./scripts/release_check.sh
```

Отдельные стадии:

```bash
./scripts/format_check.sh
./scripts/lint.sh
./scripts/test.sh
```

`release_check.sh` отличается от обычного `ci_check.sh` тем, что:
- требует `TEST_DATABASE_URL`
- отдельно прогоняет real DB integration tests
- проверяет, что в текущем Python-окружении доступны зависимости для миграций
- считается обязательным шагом перед merge/push в `main`

Подключение hooks:

```bash
./scripts/install_git_hooks.sh
```

Hooks используют:
- `.githooks/pre-commit`
- `.githooks/pre-push`

`pre-push` запускает:

```bash
./scripts/pre_push_check.sh
```

А он, в свою очередь, гоняет полный:

```bash
./scripts/ci_check.sh
```

## Границы репозитория

Здесь живут:
- backend API
- migrations
- backend tests
- deploy и release scripts
- backend docs

Здесь не живет frontend source.

Если задача про:
- landing
- docs page source
- admin UI source

нужно идти в [Wobbly-develop/front](https://github.com/Wobbly-develop/front).

## Документация

Если меняется backend API:
- обновить `README.md`
- обновить `docs/MOBILE_API.md`
- при необходимости обновить docs page source во frontend-репозитории

## Production rule

- `main` обновляется только через production release
- `main` обновляется только по прямой просьбе владельца
- любой merge или push в `main` считается релизом
- release tags: `backend/v<version>`
- если базовый tag уже занят другим коммитом, production pipeline автоматически создает `backend/v<version>-r1`, затем `-r2` и так далее
- rollback делается через GitHub Actions, не вручную на сервере

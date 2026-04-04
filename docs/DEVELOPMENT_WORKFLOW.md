# Development Workflow

Правила работы для backend-репозитория.

## Ветки

- `develop` — основная ветка разработки
- `main` — production-only ветка
- задачи делаются в коротких ветках от `develop`
- прямой `develop -> main` не используем

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
2. обновить `backend/VERSION`
3. подготовить release branch через `scripts/prepare_main_release.sh`
4. влить release branch в `main`
5. дождаться production pipeline

## Проверки и hooks

Основная команда:

```bash
./scripts/ci_check.sh
```

Подключение hooks:

```bash
./scripts/install_git_hooks.sh
```

Hooks используют:
- `.githooks/pre-commit`
- `.githooks/pre-push`

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
- release tags: `backend/v<version>`
- rollback делается через GitHub Actions, не вручную на сервере

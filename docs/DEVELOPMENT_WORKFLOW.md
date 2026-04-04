# Development Workflow

Этот файл описывает правила работы именно для backend-репозитория.

## Branching

- `develop` — основная рабочая ветка
- `main` — production-only ветка
- feature work делаем в короткоживущих ветках от `develop`
- direct merge `develop -> main` не используем

## Branch Naming

Рекомендуемые префиксы:
- `feat/`
- `fix/`
- `docs/`
- `refactor/`
- `test/`
- `chore/`

Примеры:
- `feat/auth-versioning`
- `fix/score-sync`
- `docs/deploy-notes`

## Commit Messages

Используем `Conventional Commits`.

Примеры:
- `feat(api): add readiness endpoint`
- `fix(users): reject clearing username`
- `docs(repo): update backend handoff`

## Delivery Flow

Обычный flow:
1. создать ветку от `develop`
2. сделать изменение
3. прогнать локальные проверки
4. сделать commit
5. push в свою ветку
6. влить в `develop`
7. дождаться staging pipeline

Production release:
1. убедиться, что `develop` зеленый
2. выбрать новую backend version
3. подготовить release branch через `scripts/prepare_main_release.sh`
4. влить release branch в `main`
5. дождаться production pipeline

## Проверки

Основная команда:

```bash
./scripts/ci_check.sh
```

Перед commit:
- `.githooks/pre-commit`
- `scripts/pre_commit_check.sh`

Перед push:
- `.githooks/pre-push`
- `scripts/pre_push_check.sh`

Подключение hooks:

```bash
./scripts/install_git_hooks.sh
```

## Что относится к этому репозиторию

Здесь живут:
- backend API
- migrations
- backend tests
- deploy/release scripts
- backend operational docs

Здесь не живет frontend source.

Если задача про:
- landing
- docs page source
- admin UI source

нужно идти в `https://github.com/Wobbly-develop/front`.

## Docs Rule

Если меняется backend API:
- обновлять backend docs в этом репозитории
- при необходимости обновлять frontend docs source в frontend-репозитории

Минимум проверить:
- `docs/MOBILE_API.md`
- `README.md`
- frontend repo `src/features/docs/content.ts`

## Production Rule

- `main` обновляется только по явной команде на production release
- release tags вида `backend/v<version>`
- rollback делается через GitHub Actions, а не ручным git на сервере

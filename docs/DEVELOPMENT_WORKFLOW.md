# Development Workflow

Основа процесса:
- `trunk-based development`
- `Conventional Commits 1.0.0`

## Branching

Мы работаем по `trunk-based development`.

Правила:
- `main` это trunk и всегда должен быть в рабочем состоянии
- каждая задача делается в отдельной короткоживущей ветке
- имя ветки должно отражать `type`, как в Conventional Commits
- ветка живет недолго и быстро вливается обратно в `main`

Примеры:
- `feat/api-key-auth`
- `fix/username-normalization`
- `docs/development-workflow`
- `refactor/score-service`
- `chore/deploy-script`

Рекомендуемые типы веток:
- `feat/` новая функциональность
- `fix/` исправление бага
- `docs/` документация
- `refactor/` переработка без изменения внешнего поведения
- `test/` тесты
- `chore/` инфраструктура, зависимости, рутинные изменения

## Commit Messages

Commit message оформляем по `Conventional Commits`.

Формат:
- `<type>(<optional-scope>): <description>`

Примеры:
- `feat(auth): add API key validation for write endpoints`
- `fix(username): normalize input before duplicate checks`
- `docs(workflow): describe branch naming convention`
- `refactor(score): split rate limit logic into separate module`
- `chore(deps): bump fastapi version`

## Delivery Flow

Обычный процесс работы:
1. создать ветку от `main`
2. сделать небольшое изменение
3. прогнать локальную проверку
4. сделать commit в формате Conventional Commits
5. запушить ветку
6. влить изменения обратно в `main`
7. дождаться GitHub Actions pipeline
8. если pipeline зеленый, считать deploy завершенным
9. удалить ветку локально и на remote после merge

## Our Team Rule

Для этого проекта дальше придерживаемся таких правил:
- новые задачи делаем в отдельных ветках вида `feat/...`, `fix/...`, `docs/...`, `chore/...`
- commit message всегда следует Conventional Commits
- локальные hooks должны быть включены через `./scripts/install_git_hooks.sh`
- большие задачи режем на несколько маленьких commits, если это помогает чтению истории
- `main` держим как самую актуальную и стабильную ветку
- после merge удаляем ветку локально и в GitHub
- после merge в `main` ориентируемся сначала на GitHub Actions pipeline, а не на ручной деплой
- если меняется API-контракт или поведение endpoint'ов, в том же изменении нужно обновлять `https://api.wobbly.site/api/docs`
- по мере роста API текстовую docs page нужно упрощать и перестраивать так, чтобы она оставалась удобной для чтения
- API-изменение без обновления docs считается незавершенным

## Handoff Rule

Если работа переносится в новый чат, сначала нужно прочитать:
- `docs/HANDOFF.md`
- `README.md`
- `docs/BACKEND_ROADMAP.md`
- `docs/MOBILE_API.md`
- `docs/DEPLOY.md`
- `docs/DEVELOPMENT_WORKFLOW.md`

Не надо заново угадывать:
- как называется продовый сервис
- где лежит код на сервере
- какой домен обслуживает API
- через что реально деплоится production

## Handoff Checklist

Перед тем как начинать новый анализ после переноса контекста:
1. прочитать `docs/HANDOFF.md`
2. прочитать основные `.md` файлы
3. сверить локальное состояние через `git status --short --branch`
4. если задача связана с production, сначала прочитать `docs/DEPLOY.md`
5. только потом смотреть код и делать выводы

Если задача связана с production, не нужно сначала исследовать сервер через поиск:
- `find / ...`
- `grep -R /etc/...`
- случайный перебор `docker compose`, `systemd` и путей

Это уже известно и зафиксировано в `docs/DEPLOY.md`.

## Production Knowledge Rule

Для этого проекта считаем зафиксированными такие факты:
- live app path: `/opt/rating-service`
- live service: `rating-service.service`
- reverse proxy: `nginx`
- main site host: `wobbly.site`
- API host: `api.wobbly.site`
- deploy access: `root@api.wobbly.site` через `deploy_key`
- primary deploy path сейчас это GitHub Actions pipeline
- ручной fallback deploy это `scp`/копирование файлов + `systemctl restart rating-service`

Если эти факты не опровергнуты явным изменением в репозитории или на сервере, не надо их перепроверять с нуля.

## Architecture Rule

После второго этапа рефакторинга:
- `app/main.py` должен оставаться тонким entrypoint
- новые route changes должны идти в `app/api/routes/`
- dependencies должны идти в `app/api/dependencies.py`
- business logic должна идти в `app/services/`
- schemas должны идти в `app/domain/`
- core utilities должны идти в `app/core/`

Если новая задача снова раздувает `app/main.py`, это признак, что изменение кладется не туда.

## Local Hooks Rule

В проекте есть локальный обязательный guard перед коммитом:
- `.githooks/pre-commit`
- `scripts/pre_commit_check.sh`
- `.githooks/pre-push`
- `scripts/pre_push_check.sh`

Он делает:
- `ruff check --fix`
- повторную проверку `ruff`
- Python syntax checks
- JavaScript syntax checks

Подключение hooks:

```bash
./scripts/install_git_hooks.sh
```

Что проверяется локально:
- `pre-commit`:
  - `ruff check --fix`
  - повторная проверка `ruff`
  - Python syntax checks
  - JavaScript syntax checks
- `pre-push`:
  - `pytest`

В CI остаются:
- `docker compose config`
- docs sync check

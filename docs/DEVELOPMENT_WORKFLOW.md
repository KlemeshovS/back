# Development Workflow

Основа процесса:
- `feature -> develop -> release branch -> main`
- `Conventional Commits 1.0.0`

## Branching

Мы работаем через основную ветку разработки `develop`, отдельную временную release-ветку и отдельную production-ветку `main`.

Правила:
- `develop` это основная ветка разработки
- `develop` всегда должна быть в рабочем состоянии и готова к staging deploy
- `main` используется только для production release и должна отражать только production-реальность
- в `main` не вливаем изменения без явной команды пользователя на релиз
- direct merge `develop -> main` больше не используем
- production release идет через отдельную release-ветку, собранную из `develop`
- каждая задача делается в отдельной короткоживущей ветке
- имя ветки должно отражать `type`, как в Conventional Commits
- ветка живет недолго и быстро вливается обратно в `develop`

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
1. создать ветку от `develop`
2. сделать небольшое изменение
3. прогнать локальную проверку
4. сделать commit в формате Conventional Commits
5. запушить ветку
6. влить изменения обратно в `develop`
7. дождаться staging pipeline
8. если staging pipeline зеленый, считать staging deploy завершенным
9. когда пользователь явно запросил production release, из `develop` подготовить release-ветку через `scripts/prepare_main_release.sh`
10. в release-ветке убрать staging-only хвосты и проверить production-facing docs
11. влить release-ветку в `main`
12. дождаться production pipeline
13. если production pipeline зеленый, считать релиз завершенным
14. удалить release-ветку локально и на remote после merge

## Our Team Rule

Для этого проекта дальше придерживаемся таких правил:
- новые задачи делаем в отдельных ветках вида `feat/...`, `fix/...`, `docs/...`, `chore/...`
- commit message всегда следует Conventional Commits
- локальные hooks должны быть включены через `./scripts/install_git_hooks.sh`
- большие задачи режем на несколько маленьких commits, если это помогает чтению истории
- `develop` держим как самую актуальную ветку разработки
- `main` держим как production-only ветку
- без явного запроса пользователя `main` не обновляем
- если пользователь не просил production release буквально и явно, любые изменения фиксируем только в `develop`
- после merge удаляем ветку локально и в GitHub
- после merge в `develop` ориентируемся сначала на staging GitHub Actions pipeline
- после merge в `main` ориентируемся сначала на production GitHub Actions pipeline
- staging-only workflow, systemd/nginx templates и operational docs не должны попадать в `main`
- production-facing markdown в `main` должен описывать production, а не staging
- admin UI считаем единым frontend shell; различие между `production` и `staging` должно быть только в API-окружении
- если меняется API-контракт или поведение endpoint'ов, в том же изменении нужно обновлять `https://api.wobbly.site/api/docs`
- по мере роста API текстовую docs page нужно упрощать и перестраивать так, чтобы она оставалась удобной для чтения
- API-изменение без обновления docs считается незавершенным
- источником правды для docs page в текущей структуре считается `frontend/src/features/docs/content.ts`

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

И использовать эти правила как source of truth, пока репозиторий не показывает явное изменение процесса.

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
- staging app path: `/opt/rating-service-staging`
- staging service: `rating-service-staging.service`
- reverse proxy: `nginx`
- main site host: `wobbly.site`
- API host: `api.wobbly.site`
- staging API host: `staging-api.wobbly.site`
- admin host: `admin.wobbly.site`
- deploy access: `root@api.wobbly.site` через `deploy_key`
- primary deploy path сейчас это GitHub Actions pipeline
- `develop` деплоится в staging
- release branch вливается в `main`, и только `main` деплоится в production
- ручной fallback deploy это `scp`/копирование файлов + `systemctl restart rating-service`

И дополнительно:
- production docs page живет на `https://api.wobbly.site/api/docs`
- источник правды для docs page: `frontend/src/features/docs/content.ts`
- production docs page должна грузить assets через `/assets/...`
- landing page production-facing truth живет на `https://wobbly.site`

## Release Branch Rule

Перед production release:
1. перейти на `develop`
2. убедиться, что дерево чистое
3. запустить `./scripts/prepare_main_release.sh`
4. просмотреть release-ветку
5. закоммитить cleanup staging-only файлов
6. только потом вливать release-ветку в `main`

Если пользователь просит production release "прямо сейчас", это не отменяет release branch rule.

Если эти факты не опровергнуты явным изменением в репозитории или на сервере, не надо их перепроверять с нуля.

## Architecture Rule

После второго этапа рефакторинга:
- `backend/app/main.py` должен оставаться тонким entrypoint
- новые route changes должны идти в `backend/app/api/routes/`
- dependencies должны идти в `backend/app/api/dependencies.py`
- business logic должна идти в `backend/app/services/`
- schemas должны идти в `backend/app/domain/`
- core utilities должны идти в `backend/app/core/`
- frontend changes должны идти в `frontend/src/`
- page-level Vue screens должны жить в `frontend/src/pages/`
- admin UI state и typed API calls должны жить в `frontend/src/features/admin/`
- admin UI задачи должны в первую очередь смотреть в:
  - `frontend/src/pages/AdminPage.vue`
  - `frontend/src/features/admin/useAdminConsole.ts`
  - `frontend/src/features/admin/api.ts`
  - `backend/app/api/routes/admin.py`
  - `backend/app/services/admin_service.py`

Если новая задача снова раздувает `backend/app/main.py`, это признак, что изменение кладется не туда.

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
- frontend ESLint/Prettier checks

Подключение hooks:

```bash
./scripts/install_git_hooks.sh
```

Что проверяется локально:
- `pre-commit`:
  - `ruff check --fix`
  - повторная проверка `ruff`
  - Python syntax checks
  - frontend ESLint
  - frontend Prettier
- `pre-push`:
  - `pytest`
  - frontend build

В CI остаются:
- `docker compose config`
- docs sync check

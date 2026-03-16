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

Если изменение большое, можно добавить scope в хвост имени ветки:
- `feat/api-auth`
- `fix/leaderboard-sorting`
- `chore/github-actions`

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

Основные типы:
- `feat` новая функциональность
- `fix` исправление бага
- `docs` документация
- `refactor` внутреннее улучшение без новой фичи и без bug fix
- `test` тесты
- `chore` обслуживание проекта

Правила:
- описание в нижнем регистре
- коротко и по делу
- без абстрактных формулировок
- если есть `BREAKING CHANGE`, это указывается отдельно по правилам Conventional Commits

Плохие примеры:
- `fix`
- `updates`
- `changes`
- `feat: stuff`

## Shared Naming Rule

Мы теперь отталкиваемся от одной и той же семантики в нескольких местах:
- имя ветки использует тот же `type`, что и Conventional Commits
- commit message использует Conventional Commits
- по возможности PR title использует тот же формат

Это дает единый язык для изменений:
- `feat/...` значит новая возможность
- `fix/...` значит исправление
- `docs/...` значит документация

В итоге по одной только ветке и коммиту уже видно, что за изменение идет в `main`.

## Delivery Flow

Обычный процесс работы:
1. создать ветку от `main`
2. сделать небольшое изменение
3. прогнать проверку
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
- большие задачи режем на несколько маленьких commits, если это помогает чтению истории
- `main` держим как самую актуальную и стабильную ветку
- после merge удаляем ветку локально и в GitHub
- после merge в `main` ориентируемся сначала на GitHub Actions pipeline, а не на ручной деплой
- если меняется API-контракт или поведение endpoint'ов, в том же изменении нужно обновлять `https://api.wobbly.site/api/docs`
- по мере роста API текстовую docs page нужно упрощать и перестраивать так, чтобы она оставалась удобной для чтения

## Handoff Rule

Если работа переносится в новый чат, сначала нужно прочитать:
- `README.md`
- `BACKEND_ROADMAP.md`
- `MOBILE_API.md`
- `DEPLOY.md`
- `DEVELOPMENT_WORKFLOW.md`

Не надо заново угадывать:
- как называется продовый сервис
- где лежит код на сервере
- какой домен обслуживает API
- через что реально деплоится production

## Handoff Checklist

Перед тем как начинать новый анализ после переноса контекста:
1. прочитать основные `.md` файлы
2. сверить локальное состояние через `git status --short --branch`
3. если задача связана с production, сначала прочитать `DEPLOY.md`
4. только потом смотреть код и делать выводы

Если задача связана с production, не нужно сначала исследовать сервер через поиск:
- `find / ...`
- `grep -R /etc/...`
- случайный перебор `docker compose`, `systemd` и путей

Это уже известно и зафиксировано в `DEPLOY.md`.

## Production Knowledge Rule

Для этого проекта считаем зафиксированными такие факты:
- live app path: `/opt/rating-service`
- live service: `rating-service.service`
- reverse proxy: `nginx`
- main site host: `wobbly.site`
- API host: `api.wobbly.site`
- deploy access: `root@api.wobbly.site` через `deploy_key`
- production deploy сейчас это `scp`/копирование файлов + `systemctl restart rating-service`

Если эти факты не опровергнуты явным изменением в репозитории или на сервере, не надо их перепроверять с нуля.

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
7. удалить ветку локально и на remote после merge

## Our Team Rule

Для этого проекта дальше придерживаемся таких правил:
- новые задачи делаем в отдельных ветках вида `feat/...`, `fix/...`, `docs/...`, `chore/...`
- commit message всегда следует Conventional Commits
- большие задачи режем на несколько маленьких commits, если это помогает чтению истории
- `main` держим как самую актуальную и стабильную ветку
- после merge удаляем ветку локально и в GitHub

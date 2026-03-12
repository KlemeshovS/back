# Development Workflow

## Branching

Мы работаем по `trunk-based development`.

Правила:
- `main` это trunk и всегда должен быть в рабочем состоянии
- каждая задача делается в отдельной короткоживущей ветке
- имя ветки: `codex/<short-task-name>`
- ветка живет недолго и быстро вливается обратно в `main`

Примеры:
- `codex/api-key-auth`
- `codex/add-score-history`
- `codex/fix-username-validation`

## Commit Messages

Commit message должен коротко и понятно говорить, что именно сделано.

Формат:
- первая строка: краткое действие в imperative mood
- при необходимости ниже 1-3 строки с уточнением

Примеры:
- `Add rate limiting for registration and score updates`
- `Allow Cyrillic usernames`
- `Add API key authentication for write endpoints`

Если задача состоит из нескольких заметных частей, в commit message лучше явно писать результат, а не абстрактное `update` или `fix stuff`.

Плохие примеры:
- `fix`
- `updates`
- `changes`

## Delivery Flow

Обычный процесс работы:
1. создать ветку от `main`
2. сделать небольшое изменение
3. прогнать проверку
4. сделать понятный commit
5. запушить ветку
6. влить изменения обратно в `main`

## Our Team Rule

Для этого проекта дальше придерживаемся таких правил:
- новые задачи делаем в отдельных ветках `codex/...`
- commit message всегда пишет, что именно сделано
- большие задачи режем на несколько маленьких commits, если это помогает чтению истории
- `main` держим как самую актуальную и стабильную ветку

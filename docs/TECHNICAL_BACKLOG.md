# Technical Backlog

Технический backlog для backend-репозитория.

Правила:
- сюда попадают только инженерные задачи
- продуктовые формулировки выносятся отдельно
- выполненные задачи нужно либо удалять, либо переносить в release notes

## API и доменная модель

- [ ] Добавить server source of truth для собственного `score`
  - Вариант 1: вернуть `score` в `GET /me`
  - Вариант 2: добавить отдельный `GET /me/score`
  - Закрыть проблему расхождения локального и серверного `score`

- [ ] Перевести рейтинг на authenticated-only модель
  - Guest-пользователь может смотреть рейтинги
  - Guest-пользователь не может включать участие в рейтинге
  - Guest-пользователь не может закреплять `username` для рейтинга

- [ ] Добавить social-only auth backend flow
  - Google
  - Apple
  - Yandex
  - Внутренние session / refresh tokens

- [ ] Реализовать migration flow guest -> authenticated user
  - Без потери `username`
  - Без потери `participateInRating`
  - Без потери `score`

- [ ] Добавить account linking/unlinking для identity providers
  - Линковка Google / Apple / Yandex к одному internal user
  - Защита от удаления последнего рабочего способа входа

## Данные и база

- [ ] Добавить историю изменения `score`
  - Таблица событий изменения score
  - Источник изменения
  - Время изменения

- [ ] Добавить DB-level ограничения для критичных user rules
  - Публичный `username` не должен быть пустым
  - Нужна валидация уникальности и допустимого формата
  - Нужна проверка допустимых значений рейтингового флага

- [ ] Добавить план cleanup для legacy anonymous users
  - Отдельная миграция/скрипт очистки
  - Правила архивирования или связывания со входом
  - План безопасного отключения старой anonymous-модели

## Тесты

- [ ] Увеличить покрытие admin API
  - Edge cases для редактирования пользователей
  - Ошибки прав доступа
  - Проверки audit log

- [ ] Добавить integration tests для release/deploy helpers
  - Проверка release version parsing
  - Проверка deploy metadata
  - Проверка release notes generation

- [ ] Добавить auth contract tests
  - Ошибки `INVALID_TOKEN`
  - Будущие social auth сценарии
  - Session restore / session revoke

## Наблюдаемость и эксплуатация

- [ ] Добавить structured logging
  - request id
  - endpoint
  - status
  - latency
  - error code

- [ ] Добавить error monitoring
  - Sentry или аналог
  - Unhandled exceptions
  - Важные warnings

- [ ] Добавить uptime / readiness monitoring
  - `/health`
  - `/ready`
  - production alerting

- [ ] Добавить automated backups
  - Регулярный `pg_dump`
  - Retention policy
  - Хранение вне сервера

## CI/CD и release management

- [ ] Добавить smoke tests для rollback workflows
  - Проверка rollback by tag
  - Проверка deploy by ref

- [ ] Добавить backend release checklist в automation-friendly формате
  - Подготовка release branch
  - Version bump
  - Verify
  - Release
  - Rollback

- [ ] Добавить защиту от release без changelog
  - Проверка release notes перед production deploy

## Документация

- [ ] Поддерживать `MOBILE_API.md` синхронно с backend-контрактом
  - Любой API breaking/behavior change должен отражаться в docs

- [ ] Добавить короткий troubleshooting guide
  - INVALID_TOKEN
  - score drift
  - staging/prod deploy failures
  - browser cache issues для docs/admin

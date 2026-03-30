export interface DocsCard {
  method?: string;
  badgeClass?: string;
  path?: string;
  headers?: string;
  request?: string;
  response?: string;
  paragraphs?: string[];
  muted?: string;
  list?: string[];
}

export interface QuickItem {
  title: string;
  body: string;
}

export interface DocsSection {
  id: string;
  title: string;
  quickGrid?: QuickItem[];
  cards?: DocsCard[];
}

export const docsSections: DocsSection[] = [
  {
    id: "base",
    title: "Base URL",
    cards: [
      {
        response: "https://api.wobbly.site/api/v1",
        muted:
          "Для нового mobile-контракта используйте /api/v1. Legacy unversioned routes пока сохранены для обратной совместимости.",
      },
    ],
  },
  {
    id: "flow",
    title: "Интеграционный Flow",
    quickGrid: [
      {
        title: "1. Первый запуск",
        body: "Вызвать POST /api/v1/auth/anonymous, сохранить accessToken и userId.",
      },
      {
        title: "2. Загрузка профиля",
        body: "Вызвать GET /api/v1/me и определить, задан ли username и включен ли рейтинг.",
      },
      {
        title: "3. Сохранение профиля",
        body: "Вызвать PATCH /api/v1/me/profile с username и participateInRating.",
      },
      {
        title: "4. Участие в рейтинге",
        body: "Вызвать PATCH /api/v1/me/rating, чтобы отдельно включить или выключить рейтинг.",
      },
      {
        title: "5. Обновление рейтинга",
        body: "Вызвать POST /api/v1/me/score и передать только score.",
      },
    ],
  },
  {
    id: "versioning",
    title: "Versioning Strategy",
    cards: [
      {
        paragraphs: [
          "Новый публичный mobile-контракт начинается с /api/v1/...",
          "Старые unversioned routes пока остаются доступными, чтобы не сломать уже выпущенных клиентов.",
          "Все обратно совместимые изменения можно добавлять в v1.",
          "Любое несовместимое изменение должно идти только через новый namespace вроде /api/v2/... с отдельным migration window для клиентов.",
        ],
      },
    ],
  },
  {
    id: "maintenance",
    title: "Правило Поддержки Docs",
    cards: [
      {
        paragraphs: [
          "Если меняется API-контракт, страницу /api/docs нужно обновлять в том же изменении.",
          "Документация должна оставаться читаемой: по смысловым секциям, без длинной неструктурированной стены текста.",
        ],
      },
    ],
  },
  {
    id: "health",
    title: "Service Health",
    cards: [
      {
        method: "GET",
        badgeClass: "get",
        path: "/health",
        paragraphs: ["Показывает, что HTTP-приложение запущено и отвечает."],
        response: `{
  "status": "ok"
}`,
      },
      {
        method: "GET",
        badgeClass: "get",
        path: "/ready",
        paragraphs: [
          "Показывает, что сервис реально готов принимать трафик.",
          "Сейчас readiness проверяет доступность PostgreSQL через простой DB ping.",
        ],
        response: `{
  "status": "ok"
}`,
        muted:
          "Если база недоступна, endpoint вернет 503 и единый error contract с message = Service not ready.",
      },
    ],
  },
  {
    id: "admin-api",
    title: "Admin API",
    cards: [
      {
        paragraphs: [
          "Для админки есть отдельный набор endpoint'ов под /admin.",
          "Admin auth не заменяет обычный user auth. Это отдельный слой для панели управления.",
          "Основные методы: POST /admin/auth/login, POST /admin/auth/logout, GET /admin/me, PATCH /admin/me/password, GET /admin/overview, GET/PATCH/DELETE /admin/users, GET /admin/audit-log, GET/POST/PATCH/DELETE /admin/admin-users.",
        ],
        muted:
          "UI админки работает через admin.wobbly.site/production/ и admin.wobbly.site/staging/ с same-origin admin API /production/api/... и /staging/api/....",
      },
    ],
  },
  {
    id: "errors-contract",
    title: "Единый Формат Ошибок",
    cards: [
      {
        paragraphs: ["Все ошибки API возвращаются в формате code + message."],
        response: `{
  "code": "USERNAME_ALREADY_EXISTS",
  "message": "Username already exists"
}`,
      },
    ],
  },
  {
    id: "auth-anonymous",
    title: "POST /api/v1/auth/anonymous",
    cards: [
      {
        method: "POST",
        badgeClass: "post",
        path: "/api/v1/auth/anonymous",
        paragraphs: ["Создает anonymous user и возвращает bearer token."],
        request: "{}",
        response: `{
  "userId": 26,
  "accessToken": "rt_xxxxx",
  "tokenType": "bearer"
}`,
      },
    ],
  },
  {
    id: "me",
    title: "GET /api/v1/me",
    cards: [
      {
        method: "GET",
        badgeClass: "get",
        path: "/api/v1/me",
        headers: "Authorization: Bearer <accessToken>",
        response: `{
  "id": 26,
  "username": null,
  "participateInRating": false
}`,
      },
    ],
  },
  {
    id: "profile",
    title: "PATCH /api/v1/me/profile",
    cards: [
      {
        method: "PATCH",
        badgeClass: "patch",
        path: "/api/v1/me/profile",
        headers: `Authorization: Bearer <accessToken>
Content-Type: application/json`,
        request: `{
  "username": "player_1",
  "participateInRating": true
}`,
        response: `{
  "id": 26,
  "username": "player_1",
  "participateInRating": true
}`,
        list: [
          "Если participateInRating = true, username должен быть заполнен.",
          "username должен быть уникальным.",
          "Разрешены только латиница, цифры, _, ., -.",
        ],
      },
    ],
  },
  {
    id: "rating",
    title: "PATCH /api/v1/me/rating",
    cards: [
      {
        method: "PATCH",
        badgeClass: "patch",
        path: "/api/v1/me/rating",
        headers: `Authorization: Bearer <accessToken>
Content-Type: application/json`,
        request: `{
  "participateInRating": false
}`,
        response: `{
  "id": 26,
  "username": "player_1",
  "participateInRating": false
}`,
      },
    ],
  },
  {
    id: "score",
    title: "POST /api/v1/me/score",
    cards: [
      {
        method: "POST",
        badgeClass: "post",
        path: "/api/v1/me/score",
        headers: `Authorization: Bearer <accessToken>
Content-Type: application/json`,
        request: `{
  "score": 123
}`,
        response: `{
  "username": "player_1",
  "score": 123
}`,
        muted:
          "Мобильное приложение не должно передавать userId или username. Backend определяет пользователя по токену.",
      },
    ],
  },
  {
    id: "leaderboard",
    title: "Leaderboard",
    cards: [
      {
        method: "GET",
        badgeClass: "get",
        path: "/api/v1/leaderboard/top?limit=100",
        paragraphs: ["Возвращает только пользователей с score >= 0."],
      },
      {
        method: "GET",
        badgeClass: "get",
        path: "/api/v1/leaderboard/bottom?limit=100",
        paragraphs: ["Возвращает только пользователей с score < 0."],
      },
    ],
  },
];

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
        response: "https://api.wobbly.site",
        muted:
          "Для защищенных методов передавайте Authorization: Bearer <accessToken>.",
      },
    ],
  },
  {
    id: "flow",
    title: "Интеграционный Flow",
    quickGrid: [
      {
        title: "1. Первый запуск",
        body: "Вызвать POST /auth/anonymous, сохранить accessToken и userId.",
      },
      {
        title: "2. Загрузка профиля",
        body: "Вызвать GET /me и определить, задан ли username и включен ли рейтинг.",
      },
      {
        title: "3. Сохранение профиля",
        body: "Вызвать PATCH /me/profile с username и participateInRating.",
      },
      {
        title: "4. Участие в рейтинге",
        body: "Вызвать PATCH /me/rating, чтобы отдельно включить или выключить рейтинг.",
      },
      {
        title: "5. Обновление рейтинга",
        body: "Вызвать POST /me/score и передать только score.",
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
    title: "POST /auth/anonymous",
    cards: [
      {
        method: "POST",
        badgeClass: "post",
        path: "/auth/anonymous",
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
    title: "GET /me",
    cards: [
      {
        method: "GET",
        badgeClass: "get",
        path: "/me",
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
    title: "PATCH /me/profile",
    cards: [
      {
        method: "PATCH",
        badgeClass: "patch",
        path: "/me/profile",
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
    title: "PATCH /me/rating",
    cards: [
      {
        method: "PATCH",
        badgeClass: "patch",
        path: "/me/rating",
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
    title: "POST /me/score",
    cards: [
      {
        method: "POST",
        badgeClass: "post",
        path: "/me/score",
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
        path: "/leaderboard/top?limit=100",
        paragraphs: ["Возвращает только пользователей с score >= 0."],
      },
      {
        method: "GET",
        badgeClass: "get",
        path: "/leaderboard/bottom?limit=100",
        paragraphs: ["Возвращает только пользователей с score < 0."],
      },
    ],
  },
];

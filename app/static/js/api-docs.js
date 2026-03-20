class DocsPage {
  constructor() {
    this.docsSections = [
      {
        id: "base",
        title: "Base URL",
        cards: [
          {
            pre: "https://api.wobbly.site",
            muted:
              "Для защищенных методов нужно передавать заголовок Authorization: Bearer <accessToken>.",
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
            body: "Вызвать GET /me и понять, задано ли имя и включен ли рейтинг.",
          },
          {
            title: "3. Сохранение профиля",
            body: "Вызвать PATCH /me/profile с username и participateInRating.",
          },
          {
            title: "4. Участие в рейтинге",
            body: "Вызвать PATCH /me/rating, чтобы отдельно включить или выключить участие пользователя в leaderboard.",
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
              "Если меняется API-контракт, страницу /api/docs нужно обновлять в том же изменении, что и backend.",
              "По мере роста API эта страница должна оставаться удобочитаемой: группировать методы по смыслу, упрощать объяснения и не превращаться в длинную неструктурированную стену текста.",
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
              "Для админки теперь есть отдельный набор endpoint'ов под /admin.",
              "Admin auth не заменяет обычный user auth. Это отдельный слой для панели управления.",
              "Основные методы: POST /admin/auth/login, POST /admin/auth/logout, GET /admin/me, PATCH /admin/me/password, GET /admin/overview, GET/PATCH/DELETE /admin/users, GET /admin/audit-log, GET/POST/PATCH /admin/admin-users.",
            ],
            muted:
              "UI админки работает через admin.wobbly.site/production/ и admin.wobbly.site/staging/. В браузере теперь используется same-origin admin API: /production/api/... и /staging/api/....",
          },
          {
            paragraphs: [
              "Список пользователей в админке читается через GET /admin/users.",
              "Редактирование пользователя идет через PATCH /admin/users/{userId}.",
              "Удаление пользователя идет через DELETE /admin/users/{userId}.",
              "В UI users flow собран через context menu с 3 точками: редактирование открывается в modal, удаление требует отдельного подтверждения.",
            ],
          },
        ],
      },
      {
        id: "errors-contract",
        title: "Единый Формат Ошибок",
        cards: [
          {
            paragraphs: [
              "Все ошибки API теперь возвращаются в одном формате: code + message.",
            ],
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
            list: [
              "Если participateInRating = true, у пользователя уже должен быть username.",
              "Если participateInRating = false, пользователь исключается из leaderboard.",
            ],
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
        id: "top",
        title: "GET /leaderboard/top",
        cards: [
          {
            method: "GET",
            badgeClass: "get",
            path: "/leaderboard/top?limit=100",
            paragraphs: ["Возвращает только пользователей с score >= 0."],
            response: `{
  "items": [
    {
      "username": "player_1",
      "score": 2731
    },
    {
      "username": "player_2",
      "score": 1545
    }
  ],
  "total": 20
}`,
          },
        ],
      },
      {
        id: "bottom",
        title: "GET /leaderboard/bottom",
        cards: [
          {
            method: "GET",
            badgeClass: "get",
            path: "/leaderboard/bottom?limit=100",
            paragraphs: ["Возвращает только пользователей с score < 0."],
            response: `{
  "items": [
    {
      "username": "player_10",
      "score": -12
    },
    {
      "username": "player_7",
      "score": -3
    }
  ],
  "total": 20
}`,
          },
        ],
      },
      {
        id: "errors",
        title: "Ошибки",
        cards: [
          {
            list: [
              "MISSING_AUTHORIZATION_HEADER — в запросе отсутствует заголовок Authorization: Bearer <accessToken>.",
              "INVALID_AUTHORIZATION_HEADER — заголовок Authorization передан в неправильном формате.",
              "INVALID_TOKEN — токен передан, но не найден в системе или больше невалиден.",
              "USERNAME_ALREADY_EXISTS — такое имя уже занято другим пользователем.",
              "USERNAME_REQUIRED_FOR_RATING — нельзя включить участие в рейтинге без username.",
              "USER_NOT_FOUND — пользователь не найден по переданным данным.",
              "RATE_LIMIT_EXCEEDED — слишком много запросов за короткое время, нужно повторить позже.",
              "VALIDATION_ERROR — тело запроса не прошло валидацию: не хватает полей или формат данных неверный.",
              "INTERNAL_SERVER_ERROR — внутренняя ошибка backend, стоит повторить запрос позже или проверить логи.",
            ],
          },
        ],
      },
    ];
  }

  init() {
    this.renderNavigation();
    this.renderContent();
  }

  renderNavigation() {
    const nav = document.getElementById("docs-nav");
    let html = "";
    let index = 0;

    while (index < this.docsSections.length) {
      html += this.renderNavItem(this.docsSections[index]);
      index += 1;
    }

    nav.innerHTML = html;
  }

  renderContent() {
    const content = document.getElementById("docs-content");
    let html = "";
    let index = 0;

    while (index < this.docsSections.length) {
      html += this.renderSection(this.docsSections[index]);
      index += 1;
    }

    content.innerHTML = html;
  }

  renderNavItem(section) {
    return '<a href="#' + section.id + '">' + this.escapeHtml(section.title) + "</a>";
  }

  renderSection(section) {
    let html = '<section id="' + section.id + '">';
    html += "<h2>" + this.escapeHtml(section.title) + "</h2>";
    html += this.renderQuickGrid(section.quickGrid);
    html += this.renderCards(section.cards);
    html += "</section>";

    return html;
  }

  renderQuickGrid(items) {
    let html = "";
    let index = 0;

    if (!items || !items.length) {
      return html;
    }

    html += '<div class="quick-grid">';

    while (index < items.length) {
      html += this.renderQuickBox(items[index]);
      index += 1;
    }

    html += "</div>";
    return html;
  }

  renderQuickBox(item) {
    let html = '<div class="quick-box">';
    html += "<h3>" + this.escapeHtml(item.title) + "</h3>";
    html += "<p>" + this.escapeHtml(item.body) + "</p>";
    html += "</div>";

    return html;
  }

  renderCards(cards) {
    let html = "";
    let index = 0;

    if (!cards || !cards.length) {
      return html;
    }

    while (index < cards.length) {
      html += this.renderCard(cards[index]);
      index += 1;
    }

    return html;
  }

  renderCard(card) {
    let html = '<div class="card">';

    if (card.method) {
      html +=
        '<div class="method"><span class="badge ' +
        card.badgeClass +
        '">' +
        card.method +
        "</span> <code>" +
        this.escapeHtml(card.path) +
        "</code></div>";
    }

    html += this.renderParagraphs(card.paragraphs);

    if (card.pre) {
      html += "<pre>" + this.escapeHtml(card.pre) + "</pre>";
    }

    if (card.headers) {
      html += "<h3>Headers</h3>";
      html += "<pre>" + this.escapeHtml(card.headers) + "</pre>";
    }

    if (card.request) {
      html += "<h3>Request</h3>";
      html += "<pre>" + this.escapeHtml(card.request) + "</pre>";
    }

    if (card.response) {
      html += "<h3>Response</h3>";
      html += "<pre>" + this.escapeHtml(card.response) + "</pre>";
    }

    if (card.list) {
      html += this.renderList(card.list);
    }

    if (card.muted) {
      html += '<p class="muted">' + this.escapeHtml(card.muted) + "</p>";
    }

    html += "</div>";
    return html;
  }

  renderParagraphs(paragraphs) {
    let html = "";
    let index = 0;

    if (!paragraphs || !paragraphs.length) {
      return html;
    }

    while (index < paragraphs.length) {
      html += "<p>" + this.escapeHtml(paragraphs[index]) + "</p>";
      index += 1;
    }

    return html;
  }

  renderList(items) {
    let html = "<ul>";
    let index = 0;

    while (index < items.length) {
      html += "<li>" + this.escapeHtml(items[index]) + "</li>";
      index += 1;
    }

    html += "</ul>";
    return html;
  }

  escapeHtml(value) {
    return value
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;");
  }
}

document.addEventListener("DOMContentLoaded", function onReady() {
  const docsPage = new DocsPage();
  docsPage.init();
});

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
              "200 / 201 — success",
              "401 — token missing or invalid",
              "409 — username already exists",
              "422 — invalid data",
              "429 — too many requests",
              "500 — internal server error",
            ],
          },
        ],
      },
      {
        id: "legacy",
        title: "Legacy",
        cards: [
          {
            paragraphs: [
              "Эти методы оставлены только для обратной совместимости и не должны использоваться новым мобильным приложением:",
            ],
            list: ["POST /users/register", "POST /users/score"],
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

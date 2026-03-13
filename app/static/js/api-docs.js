const docsSections = [
  {
    id: "base",
    title: "Base URL",
    cards: [
      {
        pre: "https://api.wobbly.site",
        muted:
          "Для защищенных методов нужно передавать заголовок Authorization: Bearer <access_token>.",
      },
    ],
  },
  {
    id: "flow",
    title: "Интеграционный Flow",
    quickGrid: [
      {
        title: "1. Первый запуск",
        body: "Вызвать POST /auth/anonymous, сохранить access_token и user_id.",
      },
      {
        title: "2. Загрузка профиля",
        body: "Вызвать GET /me и понять, задано ли имя и включен ли рейтинг.",
      },
      {
        title: "3. Сохранение профиля",
        body: "Вызвать PATCH /me/profile с username и participate_in_rating.",
      },
      {
        title: "4. Обновление рейтинга",
        body: "Вызвать POST /me/score и передать только score.",
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
  "user_id": 26,
  "access_token": "rt_xxxxx",
  "token_type": "bearer"
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
        headers: "Authorization: Bearer <access_token>",
        response: `{
  "id": 26,
  "username": null,
  "participate_in_rating": false
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
        headers: `Authorization: Bearer <access_token>
Content-Type: application/json`,
        request: `{
  "username": "player_1",
  "participate_in_rating": true
}`,
        response: `{
  "id": 26,
  "username": "player_1",
  "participate_in_rating": true
}`,
        list: [
          "Если participate_in_rating = true, username должен быть заполнен.",
          "username должен быть уникальным.",
          "Разрешены только латиница, цифры, _, ., -.",
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
        headers: `Authorization: Bearer <access_token>
Content-Type: application/json`,
        request: `{
  "score": 123
}`,
        response: `{
  "username": "player_1",
  "score": 123
}`,
        muted:
          "Мобильное приложение не должно передавать user_id или username. Backend определяет пользователя по токену.",
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
        response: `{
  "items": [
    {
      "username": "player_10",
      "score": 1
    },
    {
      "username": "player_7",
      "score": 3
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

function escapeHtml(value) {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function renderCard(card) {
  const parts = ['<div class="card">'];

  if (card.method) {
    parts.push(
      `<div class="method"><span class="badge ${card.badgeClass}">${card.method}</span> <code>${escapeHtml(card.path)}</code></div>`
    );
  }

  (card.paragraphs || []).forEach((paragraph) => {
    parts.push(`<p>${escapeHtml(paragraph)}</p>`);
  });

  if (card.headers) {
    parts.push("<h3>Headers</h3>");
    parts.push(`<pre>${escapeHtml(card.headers)}</pre>`);
  }

  if (card.request) {
    parts.push("<h3>Request</h3>");
    parts.push(`<pre>${escapeHtml(card.request)}</pre>`);
  }

  if (card.response) {
    parts.push("<h3>Response</h3>");
    parts.push(`<pre>${escapeHtml(card.response)}</pre>`);
  }

  if (card.list) {
    parts.push("<ul>");
    card.list.forEach((item) => parts.push(`<li>${escapeHtml(item)}</li>`));
    parts.push("</ul>");
  }

  if (card.muted) {
    parts.push(`<p class="muted">${escapeHtml(card.muted)}</p>`);
  }

  parts.push("</div>");
  return parts.join("");
}

function renderDocs() {
  const nav = document.getElementById("docs-nav");
  const content = document.getElementById("docs-content");

  nav.innerHTML = docsSections
    .map((section) => `<a href="#${section.id}">${escapeHtml(section.title)}</a>`)
    .join("");

  content.innerHTML = docsSections
    .map((section) => {
      const cards = section.cards ? section.cards.map(renderCard).join("") : "";
      const quickGrid = section.quickGrid
        ? `<div class="quick-grid">${section.quickGrid
            .map(
              (item) => `
                <div class="quick-box">
                  <h3>${escapeHtml(item.title)}</h3>
                  <p>${escapeHtml(item.body)}</p>
                </div>
              `
            )
            .join("")}</div>`
        : "";

      return `
        <section id="${section.id}">
          <h2>${escapeHtml(section.title)}</h2>
          ${quickGrid}
          ${cards}
        </section>
      `;
    })
    .join("");
}

document.addEventListener("DOMContentLoaded", renderDocs);

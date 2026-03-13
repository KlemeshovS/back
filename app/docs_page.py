DOCS_HTML = """<!DOCTYPE html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Wobbly API Docs</title>
  <style>
    :root {
      --bg: #0f1020;
      --panel: #17192b;
      --panel-2: #1f2340;
      --text: #f3f4ff;
      --muted: #b9bce0;
      --accent: #7c5cff;
      --accent-2: #31d0aa;
      --border: rgba(255, 255, 255, 0.09);
      --code: #101221;
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at top left, rgba(124, 92, 255, 0.24), transparent 30%),
        radial-gradient(circle at top right, rgba(49, 208, 170, 0.18), transparent 25%),
        var(--bg);
      color: var(--text);
      line-height: 1.55;
      overflow-x: hidden;
    }

    .layout {
      display: grid;
      grid-template-columns: 280px minmax(0, 1fr);
      min-height: 100vh;
    }

    .sidebar {
      position: sticky;
      top: 0;
      height: 100vh;
      padding: 32px 20px;
      overflow-y: auto;
      border-right: 1px solid var(--border);
      background: rgba(10, 12, 24, 0.85);
      backdrop-filter: blur(10px);
    }

    .brand {
      font-size: 28px;
      font-weight: 800;
      letter-spacing: 0.02em;
      margin-bottom: 8px;
    }

    .subtitle {
      color: var(--muted);
      margin-bottom: 24px;
      font-size: 14px;
    }

    .sidebar a {
      display: block;
      color: var(--muted);
      text-decoration: none;
      padding: 8px 10px;
      border-radius: 10px;
      margin-bottom: 6px;
    }

    .sidebar a:hover {
      color: var(--text);
      background: rgba(124, 92, 255, 0.14);
    }

    .content {
      padding: 40px 56px 80px;
      max-width: 980px;
      width: min(100%, 980px);
    }

    .hero {
      margin-bottom: 28px;
      padding: 28px;
      border: 1px solid var(--border);
      border-radius: 24px;
      background: linear-gradient(135deg, rgba(124, 92, 255, 0.16), rgba(49, 208, 170, 0.08));
    }

    h1, h2, h3 { margin-top: 0; }
    h1 { font-size: clamp(32px, 5vw, 42px); margin-bottom: 8px; }
    h2 {
      font-size: clamp(24px, 3.4vw, 28px);
      margin: 40px 0 16px;
      padding-top: 12px;
      scroll-margin-top: 16px;
    }
    h3 {
      font-size: clamp(18px, 2.4vw, 20px);
      margin: 28px 0 12px;
    }

    p, li { color: var(--text); }
    .muted { color: var(--muted); }

    .card {
      padding: 24px;
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 20px;
      margin-bottom: 18px;
    }

    .method {
      display: inline-flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      letter-spacing: 0.03em;
      margin-bottom: 10px;
    }

    .badge {
      display: inline-block;
      min-width: 62px;
      text-align: center;
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 800;
      color: white;
      background: var(--accent);
    }

    .badge.get { background: #1d9bf0; }
    .badge.post { background: #22c55e; }
    .badge.patch { background: #f59e0b; }

    code {
      font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
      background: rgba(255, 255, 255, 0.06);
      padding: 2px 6px;
      border-radius: 6px;
    }

    pre {
      margin: 12px 0 0;
      background: var(--code);
      color: #e5e7ff;
      padding: 16px;
      border-radius: 16px;
      overflow-x: auto;
      border: 1px solid var(--border);
      white-space: pre-wrap;
      word-break: break-word;
    }

    .quick-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(230px, 1fr));
      gap: 16px;
      margin-top: 18px;
    }

    .quick-box {
      background: var(--panel-2);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 18px;
    }

    .links {
      display: flex;
      flex-wrap: wrap;
      gap: 12px;
      margin-top: 18px;
    }

    .links a {
      color: var(--text);
      text-decoration: none;
      background: rgba(124, 92, 255, 0.2);
      border: 1px solid var(--border);
      padding: 10px 14px;
      border-radius: 12px;
    }

    ul {
      padding-left: 20px;
    }

    @media (max-width: 920px) {
      .layout {
        grid-template-columns: 1fr;
      }

      .sidebar {
        position: static;
        height: auto;
        border-right: 0;
        border-bottom: 1px solid var(--border);
        padding: 20px 16px 14px;
      }

      .content {
        padding: 28px 20px 60px;
      }

      .sidebar nav {
        display: flex;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 4px;
        margin: 0 -2px;
        scrollbar-width: thin;
      }

      .sidebar a {
        display: inline-flex;
        white-space: nowrap;
        margin-bottom: 0;
      }
    }

    @media (max-width: 640px) {
      .content {
        padding: 20px 14px 48px;
      }

      .hero,
      .card,
      .quick-box {
        padding: 18px;
        border-radius: 18px;
      }

      .links {
        flex-direction: column;
      }

      .links a {
        width: 100%;
        text-align: center;
      }

      .quick-grid {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Wobbly API</div>
      <div class="subtitle">Документация для мобильного приложения</div>
      <nav>
        <a href="#base">Base URL</a>
        <a href="#flow">Интеграционный Flow</a>
        <a href="#auth-anonymous">POST /auth/anonymous</a>
        <a href="#me">GET /me</a>
        <a href="#profile">PATCH /me/profile</a>
        <a href="#score">POST /me/score</a>
        <a href="#top">GET /leaderboard/top</a>
        <a href="#bottom">GET /leaderboard/bottom</a>
        <a href="#errors">Ошибки</a>
        <a href="#legacy">Legacy</a>
      </nav>
    </aside>

    <main class="content">
      <section class="hero">
        <h1>Wobbly API</h1>
        <p class="muted">Актуальная текстовая документация для мобильного приложения. Swagger доступен отдельно и подходит для ручного тестирования.</p>
        <div class="links">
          <a href="/api/swagger">Открыть Swagger</a>
          <a href="/api/openapi.json">OpenAPI JSON</a>
        </div>
      </section>

      <section id="base">
        <h2>Base URL</h2>
        <div class="card">
          <pre>https://api.wobbly.site</pre>
          <p class="muted">Для защищенных методов нужно передавать заголовок <code>Authorization: Bearer &lt;access_token&gt;</code>.</p>
        </div>
      </section>

      <section id="flow">
        <h2>Интеграционный Flow</h2>
        <div class="quick-grid">
          <div class="quick-box">
            <h3>1. Первый запуск</h3>
            <p>Вызвать <code>POST /auth/anonymous</code>, сохранить <code>access_token</code> и <code>user_id</code>.</p>
          </div>
          <div class="quick-box">
            <h3>2. Загрузка профиля</h3>
            <p>Вызвать <code>GET /me</code> и понять, задано ли имя и включен ли рейтинг.</p>
          </div>
          <div class="quick-box">
            <h3>3. Сохранение профиля</h3>
            <p>Вызвать <code>PATCH /me/profile</code> с <code>username</code> и <code>participate_in_rating</code>.</p>
          </div>
          <div class="quick-box">
            <h3>4. Обновление рейтинга</h3>
            <p>Вызвать <code>POST /me/score</code> и передать только <code>score</code>.</p>
          </div>
        </div>
      </section>

      <section id="auth-anonymous">
        <h2>POST /auth/anonymous</h2>
        <div class="card">
          <div class="method"><span class="badge post">POST</span> <code>/auth/anonymous</code></div>
          <p>Создает anonymous user и возвращает bearer token.</p>
          <h3>Request</h3>
          <pre>{}</pre>
          <h3>Response</h3>
          <pre>{
  "user_id": 26,
  "access_token": "rt_xxxxx",
  "token_type": "bearer"
}</pre>
        </div>
      </section>

      <section id="me">
        <h2>GET /me</h2>
        <div class="card">
          <div class="method"><span class="badge get">GET</span> <code>/me</code></div>
          <h3>Headers</h3>
          <pre>Authorization: Bearer &lt;access_token&gt;</pre>
          <h3>Response</h3>
          <pre>{
  "id": 26,
  "username": null,
  "participate_in_rating": false
}</pre>
        </div>
      </section>

      <section id="profile">
        <h2>PATCH /me/profile</h2>
        <div class="card">
          <div class="method"><span class="badge patch">PATCH</span> <code>/me/profile</code></div>
          <h3>Headers</h3>
          <pre>Authorization: Bearer &lt;access_token&gt;
Content-Type: application/json</pre>
          <h3>Request</h3>
          <pre>{
  "username": "player_1",
  "participate_in_rating": true
}</pre>
          <h3>Response</h3>
          <pre>{
  "id": 26,
  "username": "player_1",
  "participate_in_rating": true
}</pre>
          <h3>Правила</h3>
          <ul>
            <li>Если <code>participate_in_rating = true</code>, <code>username</code> должен быть заполнен.</li>
            <li><code>username</code> должен быть уникальным.</li>
            <li>Разрешены только латиница, цифры, <code>_</code>, <code>.</code>, <code>-</code>.</li>
          </ul>
        </div>
      </section>

      <section id="score">
        <h2>POST /me/score</h2>
        <div class="card">
          <div class="method"><span class="badge post">POST</span> <code>/me/score</code></div>
          <h3>Headers</h3>
          <pre>Authorization: Bearer &lt;access_token&gt;
Content-Type: application/json</pre>
          <h3>Request</h3>
          <pre>{
  "score": 123
}</pre>
          <h3>Response</h3>
          <pre>{
  "username": "player_1",
  "score": 123
}</pre>
          <p class="muted">Мобильное приложение не должно передавать <code>user_id</code> или <code>username</code>. Backend определяет пользователя по токену.</p>
        </div>
      </section>

      <section id="top">
        <h2>GET /leaderboard/top</h2>
        <div class="card">
          <div class="method"><span class="badge get">GET</span> <code>/leaderboard/top?limit=100</code></div>
          <h3>Response</h3>
          <pre>{
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
}</pre>
        </div>
      </section>

      <section id="bottom">
        <h2>GET /leaderboard/bottom</h2>
        <div class="card">
          <div class="method"><span class="badge get">GET</span> <code>/leaderboard/bottom?limit=100</code></div>
          <h3>Response</h3>
          <pre>{
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
}</pre>
        </div>
      </section>

      <section id="errors">
        <h2>Ошибки</h2>
        <div class="card">
          <ul>
            <li><code>200</code> / <code>201</code> — success</li>
            <li><code>401</code> — token missing or invalid</li>
            <li><code>409</code> — username already exists</li>
            <li><code>422</code> — invalid data</li>
            <li><code>429</code> — too many requests</li>
            <li><code>500</code> — internal server error</li>
          </ul>
        </div>
      </section>

      <section id="legacy">
        <h2>Legacy Endpoints</h2>
        <div class="card">
          <p>Эти методы оставлены только для обратной совместимости и не должны использоваться новым мобильным приложением:</p>
          <ul>
            <li><code>POST /users/register</code></li>
            <li><code>POST /users/score</code></li>
          </ul>
        </div>
      </section>
    </main>
  </div>
</body>
</html>
"""

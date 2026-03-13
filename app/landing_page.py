APP_STORE_URL = (
    "https://apps.apple.com/ru/app/"
    "wobbly-sobriety-tracker/id6755603610?l=en-GB"
)


TRANSLATIONS = {
    "ru": {
        "lang": "ru",
        "title": "Wobbly",
        "eyebrow": "Трезвость без скуки",
        "headline": "Привет, хочешь отслеживать свои алко-загулы без занудства?",
        "body": (
            "Wobbly помогает замечать ритм, считать дни, держать фокус и "
            "спокойно возвращаться в контроль."
        ),
        "cta": "Скачать в App Store",
        "hint": "Нажми на кнопку ниже и установи приложение по иконке App Store.",
        "badge_top": "Download on the",
        "badge_bottom": "App Store",
        "feature_1_title": "Простой старт",
        "feature_1_body": "Открыл приложение, отметил день, пошел дальше без лишних экранов.",
        "feature_2_title": "Понятная динамика",
        "feature_2_body": "Видно, где ты держишься ровно, а где начинаются качели.",
        "feature_3_title": "Мягкая мотивация",
        "feature_3_body": "Без давления и морализаторства, только честная картина.",
        "footer": "Сайт Wobbly. Скачивание доступно в App Store.",
    },
    "en": {
        "lang": "en",
        "title": "Wobbly",
        "eyebrow": "Sobriety without the lecture",
        "headline": "Hi, looking for an easy way to track your drinking streaks and slips?",
        "body": (
            "Wobbly helps you spot patterns, count days, stay focused, and "
            "get back in control without turning the experience into a chore."
        ),
        "cta": "Download on the App Store",
        "hint": "Use the button below and install the app from the App Store.",
        "badge_top": "Download on the",
        "badge_bottom": "App Store",
        "feature_1_title": "Quick start",
        "feature_1_body": "Open the app, log the day, move on without extra friction.",
        "feature_2_title": "Clear progress",
        "feature_2_body": "See where you stay steady and where the pattern starts to wobble.",
        "feature_3_title": "Gentle motivation",
        "feature_3_body": "No lecturing, no pressure, just a clearer picture.",
        "footer": "Wobbly website. Download available on the App Store.",
    },
}


def render_landing_page(locale: str) -> str:
    copy = TRANSLATIONS[locale]

    return f"""<!DOCTYPE html>
<html lang="{copy["lang"]}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{copy["title"]}</title>
  <meta
    name="description"
    content="{copy["body"]}"
  />
  <style>
    :root {{
      --bg: #080816;
      --panel: rgba(16, 18, 34, 0.82);
      --panel-border: rgba(255, 255, 255, 0.12);
      --text: #f7f4ff;
      --muted: #c6bfd9;
      --violet: #7a56ff;
      --violet-2: #a56aff;
      --aqua: #5ae2cf;
      --rose: #ff7ecf;
      --shadow: 0 30px 80px rgba(0, 0, 0, 0.45);
    }}

    * {{ box-sizing: border-box; }}

    body {{
      margin: 0;
      min-height: 100vh;
      color: var(--text);
      font-family: ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background:
        radial-gradient(circle at 20% 10%, rgba(122, 86, 255, 0.34), transparent 25%),
        radial-gradient(circle at 80% 0%, rgba(255, 126, 207, 0.22), transparent 24%),
        radial-gradient(circle at 50% 100%, rgba(90, 226, 207, 0.18), transparent 30%),
        linear-gradient(180deg, #0a0a18 0%, #090914 100%);
      overflow-x: hidden;
    }}

    .page {{
      width: min(1120px, calc(100% - 32px));
      margin: 0 auto;
      padding: 28px 0 56px;
    }}

    .shell {{
      position: relative;
      overflow: hidden;
      border: 1px solid var(--panel-border);
      border-radius: 32px;
      background: linear-gradient(180deg, rgba(13, 15, 30, 0.92), rgba(12, 13, 24, 0.95));
      box-shadow: var(--shadow);
    }}

    .shell::before {{
      content: "";
      position: absolute;
      inset: auto -140px -140px auto;
      width: 360px;
      height: 360px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(122, 86, 255, 0.26), transparent 68%);
      pointer-events: none;
    }}

    .shell::after {{
      content: "";
      position: absolute;
      inset: -100px auto auto -90px;
      width: 280px;
      height: 280px;
      border-radius: 999px;
      background: radial-gradient(circle, rgba(90, 226, 207, 0.18), transparent 70%);
      pointer-events: none;
    }}

    .hero {{
      display: grid;
      grid-template-columns: minmax(0, 1.15fr) minmax(290px, 0.85fr);
      gap: 28px;
      align-items: center;
      padding: 48px;
    }}

    .eyebrow {{
      display: inline-flex;
      align-items: center;
      gap: 10px;
      padding: 8px 14px;
      border-radius: 999px;
      color: var(--muted);
      font-size: 14px;
      letter-spacing: 0.04em;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .eyebrow::before {{
      content: "";
      width: 10px;
      height: 10px;
      border-radius: 50%;
      background: linear-gradient(135deg, var(--aqua), var(--violet));
      box-shadow: 0 0 18px rgba(122, 86, 255, 0.8);
    }}

    h1 {{
      margin: 18px 0 16px;
      font-size: clamp(34px, 6vw, 68px);
      line-height: 0.98;
      letter-spacing: -0.04em;
      max-width: 11ch;
    }}

    .lead {{
      max-width: 58ch;
      color: var(--muted);
      font-size: clamp(16px, 2vw, 19px);
    }}

    .actions {{
      display: flex;
      flex-wrap: wrap;
      gap: 14px;
      margin-top: 28px;
      align-items: center;
    }}

    .app-store {{
      display: inline-flex;
      align-items: center;
      gap: 14px;
      padding: 13px 18px;
      min-height: 64px;
      border-radius: 18px;
      text-decoration: none;
      color: white;
      background: #050505;
      border: 1px solid rgba(255, 255, 255, 0.16);
      box-shadow: 0 18px 34px rgba(0, 0, 0, 0.35);
      transition: transform 180ms ease, box-shadow 180ms ease, border-color 180ms ease;
    }}

    .app-store:hover {{
      transform: translateY(-2px);
      box-shadow: 0 24px 44px rgba(0, 0, 0, 0.42);
      border-color: rgba(255, 255, 255, 0.26);
    }}

    .app-store svg {{
      width: 32px;
      height: 32px;
      flex: 0 0 auto;
    }}

    .app-store small {{
      display: block;
      opacity: 0.84;
      font-size: 12px;
      line-height: 1.1;
    }}

    .app-store strong {{
      display: block;
      font-size: 23px;
      line-height: 1.05;
      letter-spacing: -0.02em;
    }}

    .hint {{
      color: var(--muted);
      max-width: 32ch;
      font-size: 14px;
    }}

    .phone-wrap {{
      display: grid;
      place-items: center;
    }}

    .phone {{
      position: relative;
      width: min(340px, 100%);
      aspect-ratio: 0.53;
      border-radius: 38px;
      padding: 14px;
      background:
        linear-gradient(180deg, rgba(255, 255, 255, 0.18), rgba(255, 255, 255, 0.04)),
        #111321;
      box-shadow: 0 30px 60px rgba(0, 0, 0, 0.45);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .phone::before {{
      content: "";
      position: absolute;
      top: 14px;
      left: 50%;
      transform: translateX(-50%);
      width: 36%;
      height: 28px;
      border-radius: 999px;
      background: #050507;
      z-index: 2;
    }}

    .screen {{
      position: relative;
      height: 100%;
      border-radius: 28px;
      overflow: hidden;
      padding: 28px 22px;
      background:
        radial-gradient(circle at top right, rgba(165, 106, 255, 0.42), transparent 28%),
        radial-gradient(circle at 20% 0%, rgba(90, 226, 207, 0.15), transparent 18%),
        linear-gradient(180deg, #1a1535 0%, #111523 100%);
    }}

    .screen::before {{
      content: "";
      position: absolute;
      inset: 16px;
      border-radius: 22px;
      border: 1px solid rgba(255, 255, 255, 0.08);
      pointer-events: none;
    }}

    .icon {{
      width: 92px;
      height: 92px;
      border-radius: 24px;
      background:
        radial-gradient(circle at 30% 20%, rgba(255, 255, 255, 0.18), transparent 22%),
        linear-gradient(160deg, #7a56ff 0%, #a56aff 52%, #5ae2cf 100%);
      box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.18), 0 18px 30px rgba(0, 0, 0, 0.25);
      display: grid;
      place-items: center;
    }}

    .icon-mark {{
      width: 48px;
      height: 48px;
      border-radius: 999px;
      border: 7px solid rgba(255, 255, 255, 0.92);
      border-top-color: transparent;
      border-left-color: rgba(255, 255, 255, 0.58);
      transform: rotate(-18deg);
    }}

    .screen h2 {{
      margin: 18px 0 10px;
      font-size: 28px;
      line-height: 1.05;
      padding: 0;
    }}

    .screen p {{
      color: rgba(247, 244, 255, 0.8);
      font-size: 14px;
      max-width: 24ch;
    }}

    .mini-cards {{
      display: grid;
      gap: 12px;
      margin-top: 18px;
    }}

    .mini-card {{
      padding: 14px 16px;
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.08);
      backdrop-filter: blur(8px);
    }}

    .mini-card strong {{
      display: block;
      font-size: 13px;
      color: #ffffff;
      margin-bottom: 6px;
    }}

    .mini-card span {{
      color: rgba(247, 244, 255, 0.72);
      font-size: 13px;
    }}

    .features {{
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 18px;
      padding: 0 48px 48px;
    }}

    .feature {{
      padding: 22px;
      border-radius: 22px;
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }}

    .feature strong {{
      display: block;
      margin-bottom: 10px;
      font-size: 18px;
    }}

    .feature p {{
      margin: 0;
      color: var(--muted);
      font-size: 15px;
    }}

    footer {{
      padding: 0 48px 32px;
      color: rgba(198, 191, 217, 0.72);
      font-size: 13px;
    }}

    @media (max-width: 1024px) {{
      .hero {{
        grid-template-columns: 1fr;
        padding: 36px;
      }}

      .phone-wrap {{
        justify-content: start;
      }}

      .features {{
        grid-template-columns: 1fr;
        padding: 0 36px 36px;
      }}

      footer {{
        padding: 0 36px 28px;
      }}
    }}

    @media (max-width: 720px) {{
      .page {{
        width: min(100%, calc(100% - 16px));
        padding: 8px 0 28px;
      }}

      .shell {{
        border-radius: 24px;
      }}

      .hero {{
        padding: 24px 18px;
        gap: 22px;
      }}

      .actions {{
        flex-direction: column;
        align-items: stretch;
      }}

      .app-store {{
        width: 100%;
        justify-content: center;
      }}

      .hint {{
        max-width: none;
      }}

      .phone {{
        width: min(100%, 320px);
      }}

      .features {{
        padding: 0 18px 18px;
      }}

      footer {{
        padding: 0 18px 24px;
      }}
    }}
  </style>
</head>
<body>
  <main class="page">
    <section class="shell">
      <div class="hero">
        <div>
          <div class="eyebrow">{copy["eyebrow"]}</div>
          <h1>{copy["headline"]}</h1>
          <p class="lead">{copy["body"]}</p>
          <div class="actions">
            <a class="app-store" href="{APP_STORE_URL}" target="_blank" rel="noreferrer">
              <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                <path d="M16.37 12.56c.02 2.04 1.8 2.72 1.82 2.73-.02.05-.28.97-.92 1.92-.55.82-1.13 1.64-2.03 1.66-.88.02-1.16-.52-2.17-.52-1.01 0-1.32.5-2.14.54-.86.03-1.52-.87-2.08-1.69-1.15-1.66-2.02-4.68-.84-6.73.59-1.01 1.63-1.66 2.77-1.68.86-.02 1.67.58 2.18.58.51 0 1.48-.71 2.49-.61.42.02 1.61.17 2.37 1.28-.06.04-1.42.83-1.41 2.52Zm-1.92-4.94c.46-.56.78-1.35.69-2.13-.67.03-1.47.45-1.96 1.01-.43.5-.81 1.3-.71 2.06.75.06 1.52-.38 1.98-.94Z"/>
              </svg>
              <span>
                <small>{copy["badge_top"]}</small>
                <strong>{copy["badge_bottom"]}</strong>
              </span>
            </a>
            <div class="hint">{copy["hint"]}</div>
          </div>
        </div>

        <div class="phone-wrap">
          <div class="phone" aria-hidden="true">
            <div class="screen">
              <div class="icon">
                <div class="icon-mark"></div>
              </div>
              <h2>Wobbly</h2>
              <p>{copy["body"]}</p>
              <div class="mini-cards">
                <div class="mini-card">
                  <strong>{copy["feature_1_title"]}</strong>
                  <span>{copy["feature_1_body"]}</span>
                </div>
                <div class="mini-card">
                  <strong>{copy["feature_2_title"]}</strong>
                  <span>{copy["feature_2_body"]}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <section class="features">
        <article class="feature">
          <strong>{copy["feature_1_title"]}</strong>
          <p>{copy["feature_1_body"]}</p>
        </article>
        <article class="feature">
          <strong>{copy["feature_2_title"]}</strong>
          <p>{copy["feature_2_body"]}</p>
        </article>
        <article class="feature">
          <strong>{copy["feature_3_title"]}</strong>
          <p>{copy["feature_3_body"]}</p>
        </article>
      </section>

      <footer>{copy["footer"]}</footer>
    </section>
  </main>
</body>
</html>"""

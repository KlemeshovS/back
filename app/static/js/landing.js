class LandingPage {
  constructor() {
    this.copy = {
      ru: {
        title: "Wobbly",
        description:
          "Wobbly помогает отслеживать ритм, замечать срывы и спокойнее возвращаться в контроль.",
        eyebrow: "Трекер трезвости без давления",
        headline: "Следить за прогрессом проще, когда все видно в одном месте.",
        body:
          "Wobbly помогает отмечать дни, замечать повторяющиеся паттерны и держать курс без лишнего шума.",
        hint: "Приложение доступно в App Store для iPhone.",
        storeLabel: "Скачать приложение",
        badgeTop: "Download on the",
        badgeBottom: "App Store",
        ctaTitle: "Скачать Wobbly",
        ctaBody: "Откроется карточка приложения в App Store.",
        screenBody: "Короткие отметки, понятная динамика и фокус на реальном прогрессе.",
        feature1Title: "Быстрые отметки",
        feature1Body: "Зафиксируй день за пару секунд и возвращайся к своим делам.",
        feature2Title: "Ясная картина",
        feature2Body: "Сразу видно, где держится ритм и когда начинается откат.",
        feature3Title: "Спокойный тон",
        feature3Body: "Без морализаторства и давления, только полезный сигнал.",
        footer: "Wobbly доступен в App Store.",
      },
      en: {
        title: "Wobbly",
        description:
          "Wobbly helps you track your rhythm, spot slips, and get back in control with less friction.",
        eyebrow: "A sobriety tracker without the lecture",
        headline: "It is easier to stay on track when your progress is clear.",
        body:
          "Wobbly lets you log days, notice repeating patterns, and keep your focus without extra noise.",
        hint: "The app is available on the App Store for iPhone.",
        storeLabel: "Get the app",
        badgeTop: "Download on the",
        badgeBottom: "App Store",
        ctaTitle: "Download Wobbly",
        ctaBody: "This opens the app page in the App Store.",
        screenBody: "Quick check-ins, clear momentum, and a calmer view of your progress.",
        feature1Title: "Quick check-ins",
        feature1Body: "Log the day in seconds and move on.",
        feature2Title: "Clear signals",
        feature2Body: "See when your rhythm is steady and when it starts to slip.",
        feature3Title: "Gentle support",
        feature3Body: "No pressure, no lectures, just a clearer picture.",
        footer: "Wobbly is available on the App Store.",
      },
    };
    this.russianTimeZones = {
      "Europe/Moscow": true,
      "Europe/Kaliningrad": true,
      "Europe/Samara": true,
      "Asia/Yekaterinburg": true,
      "Asia/Omsk": true,
      "Asia/Krasnoyarsk": true,
      "Asia/Irkutsk": true,
      "Asia/Yakutsk": true,
      "Asia/Vladivostok": true,
      "Asia/Magadan": true,
      "Asia/Kamchatka": true,
    };
  }

  init() {
    const locale = this.detectLocale();
    this.applyCopy(locale);
  }

  detectLocale() {
    const language = (navigator.language || "").toLowerCase();
    const locale = (Intl.DateTimeFormat().resolvedOptions().locale || "").toLowerCase();
    const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";

    if (language.indexOf("ru") === 0 || locale.indexOf("ru") === 0) {
      return "ru";
    }

    if (this.russianTimeZones[timeZone]) {
      return "ru";
    }

    return "en";
  }

  applyCopy(locale) {
    const copy = this.getCopy(locale);
    const nodes = document.querySelectorAll("[data-i18n]");
    let index = 0;

    document.documentElement.lang = locale;
    document.title = copy.title;
    this.updateDescription(copy.description);

    while (index < nodes.length) {
      this.applyNodeCopy(nodes[index], copy);
      index += 1;
    }
  }

  getCopy(locale) {
    if (this.copy[locale]) {
      return this.copy[locale];
    }

    return this.copy.en;
  }

  updateDescription(descriptionText) {
    const description = document.querySelector('meta[name="description"]');

    if (description) {
      description.setAttribute("content", descriptionText);
    }
  }

  applyNodeCopy(node, copy) {
    const key = node.dataset.i18n;

    if (key && copy[key]) {
      node.textContent = copy[key];
    }
  }
}

document.addEventListener("DOMContentLoaded", function onReady() {
  const landingPage = new LandingPage();
  landingPage.init();
});

const landingCopy = {
  ru: {
    title: "Wobbly",
    description:
      "Wobbly помогает замечать ритм, считать дни, держать фокус и спокойно возвращаться в контроль.",
    eyebrow: "Трезвость без скуки",
    headline: "Привет, хочешь отслеживать свои алко-загулы без занудства?",
    body:
      "Wobbly помогает замечать ритм, считать дни, держать фокус и спокойно возвращаться в контроль.",
    hint: "Нажми на кнопку ниже и установи приложение по иконке App Store.",
    badgeTop: "Download on the",
    badgeBottom: "App Store",
    feature1Title: "Простой старт",
    feature1Body: "Открыл приложение, отметил день, пошел дальше без лишних экранов.",
    feature2Title: "Понятная динамика",
    feature2Body: "Видно, где ты держишься ровно, а где начинаются качели.",
    feature3Title: "Мягкая мотивация",
    feature3Body: "Без давления и морализаторства, только честная картина.",
    footer: "Сайт Wobbly. Скачивание доступно в App Store.",
  },
  en: {
    title: "Wobbly",
    description:
      "Wobbly helps you spot patterns, count days, stay focused, and get back in control without turning the experience into a chore.",
    eyebrow: "Sobriety without the lecture",
    headline: "Hi, looking for an easy way to track your drinking streaks and slips?",
    body:
      "Wobbly helps you spot patterns, count days, stay focused, and get back in control without turning the experience into a chore.",
    hint: "Use the button below and install the app from the App Store.",
    badgeTop: "Download on the",
    badgeBottom: "App Store",
    feature1Title: "Quick start",
    feature1Body: "Open the app, log the day, move on without extra friction.",
    feature2Title: "Clear progress",
    feature2Body: "See where you stay steady and where the pattern starts to wobble.",
    feature3Title: "Gentle motivation",
    feature3Body: "No lecturing, no pressure, just a clearer picture.",
    footer: "Wobbly website. Download available on the App Store.",
  },
};

function detectLocale() {
  const language = (navigator.language || "").toLowerCase();
  const locale = (Intl.DateTimeFormat().resolvedOptions().locale || "").toLowerCase();
  const timeZone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";

  if (
    language.startsWith("ru") ||
    locale.startsWith("ru") ||
    timeZone === "Europe/Moscow" ||
    timeZone === "Europe/Kaliningrad" ||
    timeZone === "Europe/Samara" ||
    timeZone === "Asia/Yekaterinburg" ||
    timeZone === "Asia/Omsk" ||
    timeZone === "Asia/Krasnoyarsk" ||
    timeZone === "Asia/Irkutsk" ||
    timeZone === "Asia/Yakutsk" ||
    timeZone === "Asia/Vladivostok" ||
    timeZone === "Asia/Magadan" ||
    timeZone === "Asia/Kamchatka"
  ) {
    return "ru";
  }

  return "en";
}

function applyLandingCopy(locale) {
  const copy = landingCopy[locale] || landingCopy.en;
  document.documentElement.lang = locale;
  document.title = copy.title;

  const description = document.querySelector('meta[name="description"]');
  if (description) {
    description.setAttribute("content", copy.description);
  }

  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    if (copy[key]) {
      node.textContent = copy[key];
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  applyLandingCopy(detectLocale());
});

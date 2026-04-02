<template>
  <div class="ambient ambient-a" aria-hidden="true"></div>
  <div class="ambient ambient-b" aria-hidden="true"></div>
  <div class="ambient ambient-c" aria-hidden="true"></div>

  <main class="page">
    <div class="shell">
      <header class="topbar">
        <a class="brand" href="/" aria-label="Wobbly home">
          <span class="brand-mark" aria-hidden="true"></span>
          <span class="brand-name">Wobbly</span>
        </a>
        <div class="topbar-actions">
          <a
            class="store-link"
            :href="appStoreUrl"
            target="_blank"
            rel="noreferrer"
          >
            {{ copy.navAppStore }}
          </a>
          <a
            class="store-link"
            :href="googlePlayUrl"
            target="_blank"
            rel="noreferrer"
          >
            {{ copy.navGooglePlay }}
          </a>
        </div>
      </header>

      <section class="hero">
        <div class="hero-copy">
          <div class="eyebrow">{{ copy.eyebrow }}</div>
          <h1>{{ copy.heroTitle }}</h1>
          <p class="hero-subtitle">{{ copy.heroBody }}</p>
          <div class="hero-actions">
            <div class="cta-row">
              <a
                class="primary-cta"
                :href="appStoreUrl"
                target="_blank"
                rel="noreferrer"
              >
                <span class="cta-label">{{ copy.appStoreLabel }}</span>
                <span class="cta-title">{{ copy.appStoreTitle }}</span>
              </a>
              <a
                class="secondary-cta"
                :href="googlePlayUrl"
                target="_blank"
                rel="noreferrer"
              >
                <span class="cta-label">{{ copy.googlePlayLabel }}</span>
                <span class="cta-title">{{ copy.googlePlayTitle }}</span>
              </a>
              <a
                class="secondary-cta"
                href="https://t.me/wobbly_app"
                target="_blank"
                rel="noreferrer"
              >
                <span class="cta-label">{{ copy.tgLabel }}</span>
                <span class="cta-title">{{ copy.tgTitle }}</span>
              </a>
            </div>
            <p class="hero-note">{{ copy.heroNote }}</p>
          </div>
        </div>

        <div class="hero-visual" aria-hidden="true">
          <div class="floating-card floating-card-top">
            <strong>{{ copy.feature1Title }}</strong>
            <span>{{ copy.feature1Body }}</span>
          </div>
          <div class="floating-card floating-card-middle">
            <strong>{{ copy.feature2Title }}</strong>
            <span>{{ copy.feature2Body }}</span>
          </div>
          <div class="floating-card floating-card-bottom">
            <strong>{{ copy.feature3Title }}</strong>
            <span>{{ copy.feature3Body }}</span>
          </div>
          <div class="phone phone-main">
            <div class="phone-screen">
              <div class="screen-top">
                <span class="screen-date">{{ copy.screenDate }}</span>
                <span class="screen-pill">{{ copy.screenLabel }}</span>
              </div>
              <div class="screen-score">
                <strong>{{ copy.screenNumber }}</strong>
                <span>{{ copy.screenNumberLabel }}</span>
              </div>
              <div class="screen-chart">
                <span
                  v-for="index in 7"
                  :key="index"
                  :class="`bar bar-${index}`"
                ></span>
              </div>
              <div class="screen-card">
                <strong>{{ copy.screenCardTitle }}</strong>
                <span>{{ copy.screenCardBody }}</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section class="section">
        <div class="section-heading">
          <span class="section-kicker">{{ copy.featuresKicker }}</span>
          <h2>{{ copy.featuresTitle }}</h2>
        </div>
        <div class="feature-grid">
          <article
            v-for="item in featureCards"
            :key="item.title"
            class="feature-card glass-card"
          >
            <strong>{{ item.title }}</strong>
            <p>{{ item.body }}</p>
          </article>
        </div>
      </section>

      <section class="section cta-section">
        <div class="section-heading">
          <span class="section-kicker">{{ copy.ctaKicker }}</span>
          <h2>{{ copy.ctaSectionTitle }}</h2>
          <p>{{ copy.ctaSectionBody }}</p>
        </div>
        <div class="cta-row">
          <a
            class="primary-cta"
            :href="appStoreUrl"
            target="_blank"
            rel="noreferrer"
          >
            <span class="cta-label">{{ copy.appStoreLabel }}</span>
            <span class="cta-title">{{ copy.appStoreTitle }}</span>
          </a>
          <a
            class="secondary-cta"
            :href="googlePlayUrl"
            target="_blank"
            rel="noreferrer"
          >
            <span class="cta-label">{{ copy.googlePlayLabel }}</span>
            <span class="cta-title">{{ copy.googlePlayTitle }}</span>
          </a>
          <a
            class="secondary-cta"
            href="https://t.me/wobbly_app"
            target="_blank"
            rel="noreferrer"
          >
            <span class="cta-label">{{ copy.tgLabel }}</span>
            <span class="cta-title">{{ copy.tgTitle }}</span>
          </a>
        </div>
      </section>

      <footer class="footer">
        <a href="/privacy">{{ copy.footerPrivacy }}</a>
        <a href="mailto:hello@wobbly.site">{{ copy.footerContact }}</a>
      </footer>
    </div>
  </main>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";

import "@/shared/styles/landing.css";

const appStoreUrl =
  "https://apps.apple.com/ru/app/wobbly-sobriety-tracker/id6755603610?l";
const googlePlayUrl =
  "https://play.google.com/store/apps/details?id=com.tritan.wobbly_flutter";

const locale = computed(() => {
  const language = (navigator.language || "").toLowerCase();
  return language.startsWith("ru") ? "ru" : "en";
});

const copyMap = {
  ru: {
    title: "Wobbly — минималистичный трекер трезвости",
    description:
      "Wobbly — честное зеркало твоего образа жизни: отмечай дни, смотри на цифры и не ври себе про прогресс.",
    navAppStore: "App Store",
    navGooglePlay: "Google Play",
    eyebrow: "Дерзкий sobriety tracker",
    heroTitle: "Честно отмечай дни. Смотри, кто ты на деле.",
    heroBody:
      "Wobbly — не просто трекер. Это честное зеркало твоего образа жизни: пил, тренировался или и то и другое. Цифры все запомнят.",
    appStoreLabel: "Available on iPhone",
    appStoreTitle: "Download on App Store",
    googlePlayLabel: "Available on Android",
    googlePlayTitle: "Get it on Google Play",
    tgLabel: "Join the channel",
    tgTitle: "@wobbly_app",
    heroNote: "Для iPhone и Android. Без морали. Цифры не врут.",
    feature1Title: "Быстрые отметки",
    feature1Body: "Отметь день за пару секунд.",
    feature2Title: "Понятная динамика",
    feature2Body: "Сразу видно, где держится ритм.",
    feature3Title: "Цифры не врут",
    feature3Body: "Никакой морали, только факты.",
    screenDate: "Сегодня",
    screenLabel: "straight mode",
    screenNumber: "24",
    screenNumberLabel: "дня в фокусе",
    screenCardTitle: "Ритм держится",
    screenCardBody: "Если начнешь съезжать, это будет видно сразу.",
    featuresKicker: "Почему Wobbly",
    featuresTitle: "Коротко. Жестко. По делу.",
    feature1BodyLong: "Отмечай день за пару секунд. Без форм и лишней возни.",
    feature2BodyLong:
      "Сразу видно, где держится ритм, а где тебя уже уверенно ведет в сторону.",
    feature3BodyLong:
      "Никаких мягких формулировок. Если статистика плохая, приложение не будет притворяться, что это просто этап роста.",
    ctaKicker: "Ready to start",
    ctaSectionTitle: "Начни отмечать сегодня.",
    ctaSectionBody:
      "Скачай Wobbly или залетай в Telegram. В обоих местах тебе не будут читать мораль.",
    footerPrivacy: "Privacy Policy",
    footerContact: "Contact",
  },
  en: {
    title: "Wobbly — minimal sobriety tracker",
    description:
      "Wobbly is an honest mirror for your habits: log the day, look at the numbers, and see where your real pattern is going.",
    navAppStore: "App Store",
    navGooglePlay: "Google Play",
    eyebrow: "Sharp sobriety tracker",
    heroTitle: "Log the day honestly. See who you really are.",
    heroBody:
      "Wobbly is not just a tracker. It is an honest mirror for your habits: drinking, training, or both. The numbers remember everything.",
    appStoreLabel: "Available on iPhone",
    appStoreTitle: "Download on App Store",
    googlePlayLabel: "Available on Android",
    googlePlayTitle: "Get it on Google Play",
    tgLabel: "Follow on Telegram",
    tgTitle: "@wobbly_app",
    heroNote: "Built for iPhone and Android. No lectures. Numbers do not lie.",
    feature1Title: "Quick check-ins",
    feature1Body: "Log the day in seconds.",
    feature2Title: "Clear momentum",
    feature2Body: "See where your rhythm holds.",
    feature3Title: "Numbers do not lie",
    feature3Body: "No lectures, just facts.",
    screenDate: "Today",
    screenLabel: "straight mode",
    screenNumber: "24",
    screenNumberLabel: "days in focus",
    screenCardTitle: "Rhythm looks steady",
    screenCardBody: "If you start slipping, it shows up right away.",
    featuresKicker: "Why Wobbly",
    featuresTitle: "Short. Sharp. Honest.",
    feature1BodyLong: "Log the day in seconds. No forms and no tracker bloat.",
    feature2BodyLong:
      "See where the rhythm holds and where it is already drifting off.",
    feature3BodyLong:
      "No soft language. If the stats look bad, the app will not pretend you are just going through a phase.",
    ctaKicker: "Ready to start",
    ctaSectionTitle: "Start tracking today.",
    ctaSectionBody:
      "Download Wobbly or jump into Telegram. No lectures in either place.",
    footerPrivacy: "Privacy Policy",
    footerContact: "Contact",
  },
} as const;

const copy = computed(() => copyMap[locale.value]);
const featureCards = computed(() => [
  { title: copy.value.feature1Title, body: copy.value.feature1BodyLong },
  { title: copy.value.feature2Title, body: copy.value.feature2BodyLong },
  { title: copy.value.feature3Title, body: copy.value.feature3BodyLong },
]);

onMounted(() => {
  document.title = copy.value.title;
  document
    .querySelector('meta[name="description"]')
    ?.setAttribute("content", copy.value.description);
  document
    .querySelector('meta[property="og:title"]')
    ?.setAttribute("content", copy.value.title);
  document
    .querySelector('meta[property="og:description"]')
    ?.setAttribute("content", copy.value.description);
  document
    .querySelector('meta[name="twitter:title"]')
    ?.setAttribute("content", copy.value.title);
  document
    .querySelector('meta[name="twitter:description"]')
    ?.setAttribute("content", copy.value.description);
});
</script>

<template>
  <main class="page">
    <div class="shell legal-shell">
      <header class="topbar">
        <a class="brand" href="/" aria-label="Wobbly home">
          <span class="brand-mark" aria-hidden="true"></span>
          <span class="brand-name">Wobbly</span>
        </a>
      </header>

      <section class="section legal-section">
        <div class="section-heading">
          <span class="section-kicker">Legal</span>
          <h1>Privacy Policy</h1>
        </div>
        <div class="legal-copy">
          <p>
            Wobbly stores only the data needed to provide the app experience and
            leaderboard features.
          </p>
          <p>
            If you use rating features, your public username and score may
            appear in the leaderboard shown inside the app.
          </p>
          <p>
            Anonymous authentication tokens are used to identify your app
            account and protect write actions.
          </p>
          <p>
            If you have a privacy question, contact
            <a href="mailto:hello@wobbly.site">hello@wobbly.site</a>.
          </p>
        </div>
      </section>
    </div>
  </main>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import "@/shared/styles/landing.css";

onMounted(() => {
  document.title = "Wobbly Privacy Policy";
  document
    .querySelector('meta[name="description"]')
    ?.setAttribute(
      "content",
      "Privacy policy for the Wobbly mobile application and website.",
    );
});
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="brand">Wobbly API</div>
      <div class="subtitle">Публичные и admin endpoint'ы</div>
      <a
        v-for="section in docsSections"
        :key="section.id"
        :href="`#${section.id}`"
      >
        {{ section.title }}
      </a>
    </aside>

    <main class="content">
      <section class="hero">
        <h1>API docs</h1>
        <p class="muted">
          Источник правды для человекочитаемой документации. Если меняется
          API-контракт, обновлять эту страницу нужно в том же изменении.
        </p>
        <div class="links">
          <a href="/api/swagger">Swagger UI</a>
          <a href="https://wobbly.site">Main site</a>
        </div>
      </section>

      <section
        v-for="section in docsSections"
        :id="section.id"
        :key="section.id"
      >
        <h2>{{ section.title }}</h2>
        <div v-if="section.quickGrid" class="quick-grid">
          <article
            v-for="item in section.quickGrid"
            :key="item.title"
            class="quick-box"
          >
            <h3>{{ item.title }}</h3>
            <p>{{ item.body }}</p>
          </article>
        </div>
        <article
          v-for="card in section.cards"
          :key="`${section.id}-${card.path ?? card.response}`"
          class="card"
        >
          <div v-if="card.method" class="method">
            <span class="badge" :class="card.badgeClass">{{
              card.method
            }}</span>
            <code>{{ card.path }}</code>
          </div>
          <p v-for="paragraph in card.paragraphs" :key="paragraph">
            {{ paragraph }}
          </p>
          <div v-if="card.headers">
            <h3>Headers</h3>
            <pre>{{ card.headers }}</pre>
          </div>
          <div v-if="card.request">
            <h3>Request</h3>
            <pre>{{ card.request }}</pre>
          </div>
          <div v-if="card.response">
            <h3>Response</h3>
            <pre>{{ card.response }}</pre>
          </div>
          <ul v-if="card.list">
            <li v-for="item in card.list" :key="item">{{ item }}</li>
          </ul>
          <p v-if="card.muted" class="muted">{{ card.muted }}</p>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from "vue";

import { docsSections } from "@/features/docs/content";
import "@/shared/styles/api-docs.css";

onMounted(() => {
  document.title = "Wobbly API docs";
  document
    .querySelector('meta[name="description"]')
    ?.setAttribute("content", "Human-readable API docs for Wobbly.");
});
</script>

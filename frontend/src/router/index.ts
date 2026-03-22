import { createRouter, createWebHistory } from "vue-router";

import AdminPage from "@/pages/AdminPage.vue";
import ApiDocsPage from "@/pages/ApiDocsPage.vue";
import LandingPage from "@/pages/LandingPage.vue";
import PrivacyPage from "@/pages/PrivacyPage.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "landing",
      component: LandingPage,
    },
    {
      path: "/privacy",
      name: "privacy",
      component: PrivacyPage,
    },
    {
      path: "/api/docs",
      name: "api-docs",
      component: ApiDocsPage,
    },
    {
      path: "/production/:pathMatch(.*)*",
      name: "admin-production",
      component: AdminPage,
    },
    {
      path: "/staging/:pathMatch(.*)*",
      name: "admin-staging",
      component: AdminPage,
    },
  ],
});

export default router;

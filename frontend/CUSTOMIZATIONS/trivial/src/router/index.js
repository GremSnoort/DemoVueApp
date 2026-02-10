import { createRouter, createWebHistory } from "vue-router";
import { authStore } from "@/auth/auth.store";

import LoginPage from "@/pages/LoginPage.vue";
import RegisterPage from "@/pages/RegisterPage.vue";
import RequestsListPage from "@/pages/RequestsListPage.vue";
import RequestCreatePage from "@/pages/RequestCreatePage.vue";
import AdminPage from "@/pages/AdminPage.vue";

const routes = [
  { path: "/", redirect: "/login" },

  { path: "/login", component: LoginPage, meta: { guestOnly: true } },
  { path: "/register", component: RegisterPage, meta: { guestOnly: true } },

  { path: "/requests", component: RequestsListPage, meta: { auth: true } },
  { path: "/requests/new", component: RequestCreatePage, meta: { auth: true } },

  { path: "/admin", component: AdminPage, meta: { auth: true, admin: true } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const authed = authStore.isAuthed();

  if (to.meta.auth && !authed) return "/login";
  if (to.meta.guestOnly && authed) return authStore.isAdmin() ? "/admin" : "/requests";
  if (to.meta.admin && !authStore.isAdmin()) return "/requests";
  return true;
});

export default router;

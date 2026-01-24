<script setup>
import { computed, onMounted, ref } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authStore } from "@/auth/auth.store";
import { setTheme, getTheme, initTheme } from "@/theme/theme";

const router = useRouter();
const route = useRoute();

const user = computed(() => authStore.user);
const isAuthed = computed(() => authStore.isAuthed());
const isAdmin = computed(() => authStore.isAdmin());

const theme = ref(getTheme() || "theme-light");
const themes = [
  { value: "theme-light", label: "Light" },
  { value: "theme-dark", label: "Dark" },
  { value: "theme-corporate", label: "Corporate" },
  { value: "theme-sea", label: "Sea 🌊" },
  { value: "theme-summer", label: "Summer ☀️" },
  { value: "theme-autumn", label: "Autumn 🍂" },
  { value: "theme-newyear", label: "New Year 🎄" },
];

onMounted(() => {
  // гарантируем, что при открытии страницы применится сохранённая тема
  theme.value = initTheme("theme-light");
});

function onThemeChange() {
  setTheme(theme.value);
}

function logout() {
  authStore.logout();
  router.push("/login");
}

function isActive(path) {
  return route.path === path;
}

</script>

<template>
  <header class="topbar">
    <div class="topbar__inner">
      <div class="left">
        <div class="brand" @click="$router.push(isAuthed ? '/requests' : '/login')" role="button">
          <span class="logo">◆</span>
          <span class="title">DemoVueApp</span>
        </div>

        <nav v-if="isAuthed" class="nav">
          <router-link class="navlink" :class="{ active: isActive('/requests') }" to="/requests">
            Мои заявки
          </router-link>
          <router-link class="navlink" :class="{ active: isActive('/requests/new') }" to="/requests/new">
            Создать заявку
          </router-link>

          <!-- Admin-only -->
          <router-link
            v-if="isAdmin"
            class="navlink navlink--admin"
            :class="{ active: isActive('/admin') }"
            to="/admin"
          >
            Админка
          </router-link>
        </nav>
      </div>

      <div class="right">
        <template v-if="isAuthed">
          <div class="userbox">
            <div class="who">
              <div class="login">👤 {{ user?.login }}</div>
              <div class="role" :class="{ admin: isAdmin }">
                {{ isAdmin ? "ADMIN" : "USER" }}
              </div>
            </div>
          </div>

          <select v-model="theme" @change="onThemeChange" style="padding:10px 12px;">
            <option v-for="t in themes" :key="t.value" :value="t.value">
              {{ t.label }}
            </option>
          </select>

          <button class="btn secondary" @click="logout">Выйти</button>
        </template>

        <template v-else>
          <router-link class="btnlink" to="/login">Войти</router-link>
          <router-link class="btnlink outline" to="/register">Регистрация</router-link>
        </template>
      </div>
    </div>
  </header>

  <!-- чтобы контент не залезал под fixed header -->
  <div class="topbar-spacer"></div>
</template>

<style scoped>
.topbar {
  position: sticky;
  top: 0;
  z-index: 1000;

  background: var(--topbar-bg, rgba(11, 12, 16, 0.92));
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--topbar-border, var(--border));
}

.topbar__inner {
  max-width: 980px;
  margin: 0 auto;
  padding: 12px 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}

.topbar-spacer {
  height: 8px;
}

.left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

.logo {
  width: 26px;
  height: 26px;
  display: grid;
  place-items: center;
  border-radius: 10px;

  background: var(--surface-2, var(--card-bg));
  border: 1px solid var(--border);
  font-weight: 800;
}

.title {
  font-weight: 800;
  letter-spacing: 0.2px;
}

.nav {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.navlink {
  text-decoration: none;
  padding: 8px 10px;
  border-radius: 12px;

  border: 1px solid transparent;
  opacity: 0.9;
}

.navlink:hover {
  opacity: 1;
  background: var(--hover-bg, rgba(127, 127, 127, 0.12));
  border-color: var(--border);
}

.navlink.active {
  background: var(--hover-bg, rgba(127, 127, 127, 0.12));
  border-color: var(--accent);
  opacity: 1;
}

.navlink--admin {
  border-color: color-mix(in srgb, var(--danger) 25%, transparent);
}

.navlink--admin.active {
  border-color: var(--danger);
}

.right {
  display: flex;
  align-items: center;
  gap: 10px;
  white-space: nowrap;
}

.userbox {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: 14px;

  border: 1px solid var(--border);
  background: var(--surface-2, var(--card-bg));
}

.who {
  display: grid;
  line-height: 1.1;
}

.login {
  font-weight: 700;
  font-size: 14px;
}

.role {
  font-size: 12px;
  opacity: 0.85;
}

.role.admin {
  color: color-mix(in srgb, var(--danger) 70%, var(--fg));
  font-weight: 800;
  letter-spacing: 0.4px;
}

/* кнопки-ссылки */
.btnlink {
  text-decoration: none;
  padding: 10px 14px;
  border-radius: 12px;
  background: var(--accent);
  color: var(--accent-contrast, #fff);
  font-weight: 700;
}

.btnlink.outline {
  background: transparent;
  border: 1px solid var(--border);
  color: var(--fg);
}

@media (max-width: 640px) {
  .title { display: none; }
  .userbox { display: none; }
  .nav { gap: 6px; }
  .navlink { padding: 7px 8px; }
}
</style>

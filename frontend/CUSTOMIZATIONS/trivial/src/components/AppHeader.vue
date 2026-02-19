<script setup>
import { computed } from "vue";
import { useRouter, useRoute } from "vue-router";
import { authStore } from "@/auth/auth.store";

const router = useRouter();
const route = useRoute();

const user = computed(() => authStore.user);
const isAuthed = computed(() => authStore.isAuthed());
const isAdmin = computed(() => authStore.isAdmin());

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
        <b class="brand" @click="$router.push(isAuthed ? (isAdmin ? '/admin' : '/requests') : '/login')">
          Учусь.РФ
        </b>

        <nav v-if="isAuthed" class="nav">

          <router-link class="navlink" :class="{ active: isActive('/requests') }" to="/requests">
            Мои заявки
          </router-link>

          <router-link
            v-if="!isAdmin"
            class="navlink"
            :class="{ active: isActive('/requests/new') }"
            to="/requests/new">
            Создать
          </router-link>

          <router-link
            v-if="isAdmin"
            class="navlink navlink--admin"
            :class="{ active: isActive('/admin') }"
            to="/admin"
          >
            Админка
          </router-link>

        </nav>

      </div> <!-- left -->

      <div class="right">
        <template v-if="isAuthed">
          <span class="who">👤 {{ user?.login }} ({{ isAdmin ? "admin" : "user" }})</span>
          <button class="btn secondary" @click="logout">Выйти</button>
        </template>

        <template v-else>
          <router-link class="btnlink" to="/login">Войти</router-link>
          <router-link class="btnlink outline" to="/register">Регистрация</router-link>
        </template>
      </div>
    </div>
  </header>

  <div class="topbar-spacer"></div>
</template>

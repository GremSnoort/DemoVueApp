<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { auth } from "@/auth/auth";

const router = useRouter();
const user = computed(() => auth.getUser());

function logout() {
  auth.logout();
  router.push("/login");
}
</script>

<template>
  <div class="card" style="margin-bottom: 12px;">
    <div class="row">
      <div style="display:flex; gap:12px; align-items:center;">
        <b>DemoVueApp</b>
        <router-link to="/requests">Мои заявки</router-link>
        <router-link to="/requests/new">Создать заявку</router-link>
        <router-link v-if="user?.role === 'admin'" to="/admin">Админка</router-link>
      </div>

      <div style="display:flex; gap:10px; align-items:center;">
        <span v-if="user">👤 {{ user.login }} ({{ user.role }})</span>
        <button v-if="user" class="btn secondary" @click="logout">Выйти</button>
        <router-link v-else to="/login">Войти</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
a { text-decoration: none; opacity: 0.9; }
a:hover { opacity: 1; }
</style>

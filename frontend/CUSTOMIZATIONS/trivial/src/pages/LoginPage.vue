<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";
import { authStore } from "@/auth/auth.store";

const router = useRouter();

const login = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  if (!login.value || !password.value) {
    error.value = "login and password required";
    return;
  }

  loading.value = true;
  try {
    const res = await http.post("/api/user/login", {
      login: login.value,
      password: password.value,
    });

    authStore.setAuth(res.data.token, res.data.user);

    router.push(authStore.isAdmin() ? "/admin" : "/requests");
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card">
    <h2>Авторизация</h2>

    <div v-if="error" class="err">{{ error }}</div>

    <div class="grid">
      <div class="field"><label>Логин</label><input v-model="login" /></div>
      <div class="field"><label>Пароль</label><input type="password" v-model="password" /></div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "..." : "Войти" }}
      </button>

      <router-link to="/register" style="opacity:.85;">
        Еще не зарегистрированы? Регистрация
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";
import { authStore } from "@/auth/auth.store";

const router = useRouter();

const login = ref("");
const password = ref("");
const error = ref(null);
const loading = ref(false);

async function onSubmit() {
  error.value = null;
  if (!login.value.trim() || !password.value) {
    error.value = "Введите логин и пароль";
    return;
  }

  loading.value = true;
  try {
    const res = await http.post("/auth/login", {
      login: login.value.trim(),
      password: password.value,
    });

    authStore.setAuth(res.data.token, res.data.user);
    router.push("/requests");
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

    <div v-if="error" class="err" style="margin-bottom: 10px;">{{ error }}</div>

    <div class="grid">
      <div class="field">
        <label>Логин</label>
        <input v-model="login" placeholder="user123" />
      </div>

      <div class="field">
        <label>Пароль</label>
        <input v-model="password" type="password" placeholder="••••••••" />
      </div>
    </div>

    <div style="margin-top: 12px; display:flex; gap:10px; align-items:center;">
      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? "Вход..." : "Войти" }}
      </button>

      <router-link to="/register">Еще не зарегистрированы? Регистрация</router-link>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const login = ref("");
const password = ref("");
const name = ref("");
const phone = ref("");
const email = ref("");

const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  if (!login.value || !password.value || !name.value || !phone.value || !email.value) {
    error.value = "Заполните все поля";
    return;
  }

  loading.value = true;
  try {
    await http.post("/api/user/register", {
      login: login.value,
      password: password.value,
      name: name.value,
      phone: phone.value,
      email: email.value,
    });
    router.push("/login");
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card">
    <h2>Регистрация</h2>

    <div v-if="error" class="err">{{ error }}</div>

    <div class="grid">
      <div class="field"><label>Логин</label><input v-model="login" /></div>
      <div class="field"><label>Пароль</label><input type="password" v-model="password" /></div>
      <div class="field"><label>ФИО</label><input v-model="name" /></div>
      <div class="field"><label>Телефон</label><input v-model="phone" placeholder="8(999)111-22-33" /></div>
      <div class="field"><label>Email</label><input v-model="email" /></div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "..." : "Создать пользователя" }}
      </button>

      <router-link to="/login" style="opacity:.85;">
        Уже есть аккаунт? Войти
      </router-link>
    </div>
  </div>
</template>

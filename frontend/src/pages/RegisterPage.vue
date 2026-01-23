<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const login = ref("");
const password = ref("");
const full_name = ref("");
const phone = ref("");
const email = ref("");

const error = ref(null);
const loading = ref(false);

const reLogin = /^[A-Za-z0-9]{6,}$/;
const reFullName = /^[А-Яа-яЁё ]+$/;
const rePhone = /^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/;
const reEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function validate() {
  if (!reLogin.test(login.value)) return "Логин: латиница/цифры, минимум 6 символов";
  if (password.value.length < 8) return "Пароль: минимум 8 символов";
  if (!reFullName.test(full_name.value.trim())) return "ФИО: только кириллица и пробелы";
  if (!rePhone.test(phone.value.trim())) return "Телефон: формат 8(XXX)XXX-XX-XX";
  if (!reEmail.test(email.value.trim())) return "Email: неверный формат";
  return null;
}

async function onSubmit() {
  error.value = validate();
  if (error.value) return;

  loading.value = true;
  try {
    await http.post("/auth/register", {
      login: login.value.trim(),
      password: password.value,
      full_name: full_name.value.trim(),
      phone: phone.value.trim(),
      email: email.value.trim(),
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

    <div v-if="error" class="err" style="margin-bottom: 10px;">{{ error }}</div>

    <div class="grid grid-2">
      <div class="field">
        <label>Логин</label>
        <input v-model="login" placeholder="user123" />
      </div>

      <div class="field">
        <label>Пароль</label>
        <input v-model="password" type="password" placeholder="минимум 8 символов" />
      </div>

      <div class="field">
        <label>ФИО</label>
        <input v-model="full_name" placeholder="Иванов Иван" />
      </div>

      <div class="field">
        <label>Телефон</label>
        <input v-model="phone" placeholder="8(999)111-22-33" />
      </div>

      <div class="field" style="grid-column: 1 / -1;">
        <label>Email</label>
        <input v-model="email" placeholder="u@ex.com" />
      </div>
    </div>

    <div style="margin-top: 12px; display:flex; gap:10px; align-items:center;">
      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? "Создание..." : "Создать пользователя" }}
      </button>

      <router-link to="/login">Уже есть аккаунт? Войти</router-link>
    </div>
  </div>
</template>

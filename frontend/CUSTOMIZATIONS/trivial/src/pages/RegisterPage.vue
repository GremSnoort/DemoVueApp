<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const login = ref("");
const password = ref("");
const name = ref("");
const phone = ref("");
const email = ref("");

const loading = ref(false);

// ---- REGEX ----

const reLogin = /^[A-Za-z0-9]{6,}$/;
const rePassword = /^.{8,}$/;
const reName = /^[А-Яа-яЁё\s]+$/;
const rePhone = /^8\(\d{3}\)\d{3}-\d{2}-\d{2}$/;
const reEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// ---- ERRORS ----

const errors = ref({});

function validate() {
  const e = {};

  if (!reLogin.test(login.value))
    e.login = "Логин: минимум 6 символов, латиница и цифры";

  if (!rePassword.test(password.value))
    e.password = "Пароль: минимум 8 символов";

  if (!reName.test(name.value))
    e.name = "ФИО: только кириллица и пробелы";

  if (!rePhone.test(phone.value))
    e.phone = "Телефон: формат 8(XXX)XXX-XX-XX";

  if (!reEmail.test(email.value))
    e.email = "Некорректный email";

  errors.value = e;
  return Object.keys(e).length === 0;
}

// ---- SUBMIT ----

async function submit() {
  if (!validate()) return;

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
    // если 409 от сервера
    errors.value.login = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="card">
    <h2>Регистрация</h2>

    <div class="grid">

      <div class="field">
        <label>Логин</label>
        <input v-model="login" />
        <div v-if="errors.login" class="err">{{ errors.login }}</div>
      </div>

      <div class="field">
        <label>Пароль</label>
        <input type="password" v-model="password" />
        <div v-if="errors.password" class="err">{{ errors.password }}</div>
      </div>

      <div class="field">
        <label>ФИО</label>
        <input v-model="name" placeholder="Иванов Иван Иванович" />
        <div v-if="errors.name" class="err">{{ errors.name }}</div>
      </div>

      <div class="field">
        <label>Телефон</label>
        <input v-model="phone" placeholder="8(999)111-22-33" />
        <div v-if="errors.phone" class="err">{{ errors.phone }}</div>
      </div>

      <div class="field">
        <label>Email</label>
        <input v-model="email" />
        <div v-if="errors.email" class="err">{{ errors.email }}</div>
      </div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "..." : "Создать пользователя" }}
      </button>

      <router-link to="/login" style="opacity:.85;">
        Уже есть аккаунт? Войти
      </router-link>

    </div>
  </div>
</template>

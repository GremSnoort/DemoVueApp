<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import TopSlider from "@/components/TopSlider.vue";
import { authStore } from "@/auth/auth.store";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const type = ref("service_visit");

const test1 = ref("test1");
const test2 = ref("test2");
const test3 = ref("test3");

const error = ref("");
const loading = ref(false);

async function submit() {
  error.value = "";
  loading.value = true;
  try {
    await http.post("/api/user/reqs/create", { type: type.value, payload: {
      test1: test1.value,
      test2: test2.value,
      test3: test3.value
    } });
    router.push("/requests");
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <TopSlider v-if="authStore.isAuthed()" />
  <div class="card">
    <h2>Создать заявку</h2>

    <div v-if="error" class="err">{{ error }}</div>

    <div class="grid">

      <div class="field">
        <label>Test1</label>
        <input v-model="test1" placeholder="test1" />
      </div>

      <div class="field">
        <label>Test2</label>
        <input v-model="test2" placeholder="test2" />
      </div>

      <div class="field">
        <label>Test3</label>
        <input v-model="test3" placeholder="test3" />
      </div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "..." : "Отправить" }}
      </button>
    </div>
  </div>
</template>

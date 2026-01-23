<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const type = ref("service_visit");
const payloadText = ref(`{\n  "comment": "Опишите заявку"\n}`);
const error = ref(null);
const loading = ref(false);

function parsePayload() {
  try {
    return JSON.parse(payloadText.value);
  } catch {
    throw new Error("payload должен быть валидным JSON");
  }
}

async function onSubmit() {
  error.value = null;
  if (!type.value.trim()) {
    error.value = "type обязателен";
    return;
  }

  let payload;
  try {
    payload = parsePayload();
  } catch (e) {
    error.value = e.message;
    return;
  }

  loading.value = true;
  try {
    await http.post("/requests", { type: type.value.trim(), payload });
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
    <h2>Создать заявку</h2>

    <div v-if="error" class="err" style="margin-bottom: 10px;">{{ error }}</div>

    <div class="grid">
      <div class="field">
        <label>Тип заявки</label>
        <input v-model="type" placeholder="service_visit / order / course_enroll ..." />
      </div>

      <div class="field">
        <label>Payload (JSON)</label>
        <textarea v-model="payloadText" rows="10" style="font-family: ui-monospace, Menlo, monospace;"></textarea>
      </div>

      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? "Отправка..." : "Отправить" }}
      </button>
    </div>
  </div>
</template>

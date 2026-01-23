<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";
import { getTypeTitle, makeSummary } from "@/domain/domain.utils";

const items = ref([]);
const error = ref(null);
const loading = ref(false);

const feedbackRating = ref({});
const feedbackComment = ref({});
const feedbackError = ref({});
const feedbackOk = ref({});

function pretty(v) {
  try { return JSON.stringify(v, null, 2); } catch { return String(v); }
}

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const res = await http.get("/requests");
    items.value = res.data.items || [];
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function sendFeedback(requestId) {
  feedbackError.value[requestId] = "";
  feedbackOk.value[requestId] = false;

  const rating = feedbackRating.value[requestId];
  if (!rating || rating < 1 || rating > 5) {
    feedbackError.value[requestId] = "Рейтинг должен быть 1..5";
    return;
  }

  try {
    await http.post(`/requests/${requestId}/feedback`, {
      rating,
      comment: feedbackComment.value[requestId] || null,
    });
    feedbackOk.value[requestId] = true;
  } catch (e) {
    feedbackError.value[requestId] = apiErrorMessage(e);
  }
}

onMounted(load);
</script>

<template>
  <div class="card">
    <div class="row">
      <h2 style="margin:0;">Мои заявки</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "Обновление..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">{{ error }}</div>

    <div v-if="items.length === 0 && !loading" style="opacity:0.8; margin-top:12px;">
      Заявок пока нет. Создай первую на странице “Создать заявку”.
    </div>

    <div class="grid" style="margin-top:12px;">
      <div v-for="it in items" :key="it.id" class="card">
        <div class="row">
          <div>
            <b>{{ getTypeTitle(it.type) }}</b>
            <div style="opacity:0.8; font-size: 14px;">{{ makeSummary(it.type, it.payload) }}</div>
            <div style="opacity:0.8; font-size: 14px;">ID: {{ it.id }}</div>
          </div>
          <div>
            <span class="card" style="padding:6px 10px;">Статус: <b>{{ it.status }}</b></span>
          </div>
        </div>

        <div style="margin-top:10px;">
          <div style="opacity:0.8; font-size:14px;">Payload:</div>
          <details style="margin-top:10px;">
          <summary style="cursor:pointer; opacity:0.85;">Показать детали</summary>
          <pre style="white-space: pre-wrap; margin: 8px 0 0; font-size: 13px;">{{ pretty(it.payload) }}</pre>
          </details>
        </div>

        <div v-if="it.admin_comment" style="margin-top:10px;">
          <div style="opacity:0.8; font-size:14px;">Комментарий администратора:</div>
          <div>{{ it.admin_comment }}</div>
        </div>

        <div class="card" style="margin-top:12px;">
          <b>Оставить отзыв</b>
          <div class="grid grid-2" style="margin-top:10px;">
            <div class="field">
              <label>Оценка (1..5)</label>
              <input type="number" min="1" max="5" v-model.number="feedbackRating[it.id]" />
            </div>
            <div class="field">
              <label>Комментарий</label>
              <input v-model="feedbackComment[it.id]" placeholder="Коротко о качестве" />
            </div>
          </div>

          <div v-if="feedbackError[it.id]" class="err" style="margin-top:8px;">
            {{ feedbackError[it.id] }}
          </div>
          <div v-if="feedbackOk[it.id]" style="margin-top:8px; color:#7bff9b;">
            Отзыв отправлен ✅
          </div>

          <button class="btn" style="margin-top:10px;" @click="sendFeedback(it.id)">
            Отправить отзыв
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

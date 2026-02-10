<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const rate = ref({});
const comment = ref({});
const rateErr = ref({});
const rateOk = ref({});

async function load() {
  error.value = "";
  loading.value = true;
  try {
    const res = await http.get("/api/user/reqs/list");
    items.value = res.data.items || [];
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function sendRate(id) {
  rateErr.value[id] = "";
  rateOk.value[id] = false;

  const r = rate.value[id];
  if (typeof r !== "number" || r < 0 || r > 5) {
    rateErr.value[id] = "rating must be 0..5";
    return;
  }

  try {
    await http.post(`/api/user/reqs/${id}/rate`, {
      rating: r,
      comment: comment.value[id] || null,
    });
    rateOk.value[id] = true;
  } catch (e) {
    rateErr.value[id] = apiErrorMessage(e);
  }
}

onMounted(load);
</script>

<template>
  <div class="card">
    <div class="row">
      <h2 style="margin:0;">Мои заявки</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">{{ error }}</div>

    <div v-if="items.length === 0 && !loading" style="opacity:.8; margin-top:12px;">
      Пока нет заявок.
    </div>

    <div class="grid" style="margin-top:12px;">
      <div v-for="it in items" :key="it.id" class="card">

        <div><b>{{ it.type }}</b></div>
        <div style="opacity:.8;">status: {{ it.status }}</div>

        <details style="margin-top:10px;">
          <summary style="cursor:pointer;">payload</summary>
          <pre style="white-space: pre-wrap;">{{ it.payload }}</pre>
        </details>

        <div class="card" style="margin-top:12px;">
          <b>Оставить отзыв</b>
          <div class="grid grid-2" style="margin-top:10px;">

            <div class="field">
              <label>rating (0..5)</label>
              <input type="number" min="0" max="5" v-model.number="rate[it.id]" />
            </div>

            <div class="field">
              <label>comment</label>
              <input v-model="comment[it.id]" />
            </div>

          </div>

          <div v-if="rateErr[it.id]" class="err" style="margin-top:8px;">{{ rateErr[it.id] }}</div>
          <div v-if="rateOk[it.id]" style="margin-top:8px; color: #2da44e;">OK ✅</div>

          <button class="btn" style="margin-top:10px;" @click="sendRate(it.id)">Отправить</button>
        </div>

      </div>
    </div>
  </div>
</template>

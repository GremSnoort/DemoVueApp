<script setup>
import { onMounted, ref } from "vue";
import TopSlider from "@/components/TopSlider.vue";
import { authStore } from "@/auth/auth.store";
import { http, apiErrorMessage } from "@/api/http";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const rate = ref({});
const comment = ref({});
const rateErr = ref({});
const rateOk = ref({});

function formatStatus(val) {
  const map = {
    new: "Новая",
    event_scheduled: "Запланировано",
    event_completed: "Завершено",
  };
  return map[val] || val;
}

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
    await load(); // перезагружаем список, чтобы увидеть feedback
  } catch (e) {
    rateErr.value[id] = apiErrorMessage(e);
  }
}

onMounted(load);
</script>

<template>
  <TopSlider v-if="authStore.isAuthed()" />

  <div class="card">
    <div class="row">
      <h2 style="margin:0;">Мои заявки</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">
      {{ error }}
    </div>

    <div
      v-if="items.length === 0 && !loading"
      style="opacity:.8; margin-top:12px;"
    >
      Пока нет заявок.
    </div>

    <div class="grid" style="margin-top:12px;">
      <div v-for="it in items" :key="it.id" class="card">

        <div><b>{{ it.type }}</b></div>
        <div style="opacity:.8;">Статус: {{ formatStatus(it.status) }}</div>

        <!-- payload -->
        <details style="margin-top:10px;">
          <summary style="cursor:pointer;">Данные заявки</summary>
          <pre style="white-space: pre-wrap;">{{ it.payload }}</pre>
        </details>

        <!-- Если уже есть feedback -->
        <div v-if="it.feedback" class="card" style="margin-top:12px;">
          <b>Ваш отзыв</b>

          <div style="margin-top:8px;">
            <div>Оценка: ⭐ {{ it.feedback.rating }} / 5</div>
            <div v-if="it.feedback.comment" style="margin-top:6px;">
              Комментарий: {{ it.feedback.comment }}
            </div>
          </div>
        </div>

        <!-- Если нет feedback -->
        <div v-else class="card" style="margin-top:12px;">
          <b>Оставить отзыв</b>

          <div class="grid grid-2" style="margin-top:10px;">

            <div class="field">
              <label>Оценка от 0 до 5</label>
              <input
                type="number"
                min="0"
                max="5"
                v-model.number="rate[it.id]"
              />
            </div>

            <div class="field">
              <label>Комментарий</label>
              <input v-model="comment[it.id]" />
            </div>

          </div>

          <div
            v-if="rateErr[it.id]"
            class="err"
            style="margin-top:8px;"
          >
            {{ rateErr[it.id] }}
          </div>

          <div
            v-if="rateOk[it.id]"
            style="margin-top:8px; color: #16a34a;"
          >
            OK ✅
          </div>

          <button
            class="btn"
            style="margin-top:10px;"
            @click="sendRate(it.id)"
          >
            Отправить
          </button>
        </div>

      </div>
    </div>
  </div>
</template>

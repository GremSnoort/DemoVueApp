<script setup>
import { onMounted, ref } from "vue";
import TopSlider from "@/components/TopSlider.vue";
import { authStore } from "@/auth/auth.store";
import { http, apiErrorMessage } from "@/api/http";
import { formatStatus, formatDate, formatRoomType, formatPaymentMethod } from "@/utils/formatters";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const rate = ref({});
const comment = ref({});
const rateErr = ref({});
const rateOk = ref({});

function isBanquetBooking(it) {
  return it?.type === "banquet_hall_booking";
}

function prettyPayload(payload) {
  try {
    return JSON.stringify(payload, null, 2);
  } catch {
    return String(payload);
  }
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

function ratingIsValid(id) {
  const r = rate.value[id];
  return typeof r === "number" && !Number.isNaN(r) && r >= 0 && r <= 5;
}

async function sendRate(id) {
  rateErr.value[id] = "";
  rateOk.value[id] = false;

  if (!ratingIsValid(id)) {
    rateErr.value[id] = "Оценка должна быть в диапазоне 0..5";
    return;
  }

  try {
    await http.post(`/api/user/reqs/${id}/rate`, {
      rating: rate.value[id],
      comment: comment.value[id] || null,
    });

    rateOk.value[id] = true;
    await load();
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
      <h2 style="margin: 0;">Мои заявки</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top: 10px;">
      {{ error }}
    </div>

    <div v-if="items.length === 0 && !loading" style="opacity: 0.8; margin-top: 12px;">
      Пока нет заявок.
    </div>

    <div class="grid" style="margin-top: 12px;">
      <div v-for="it in items" :key="it.id" class="card">
        <div class="row">
          <div>
            <b>
              {{ isBanquetBooking(it) ? "Бронирование зала для банкета" : it.type }}
            </b>
            <div style="opacity: 0.8; margin-top: 4px;">
              Статус: {{ formatStatus(it.status) }}
            </div>
          </div>
        </div>

        <!-- Wide row: Данные заявки + Отзыв/форма -->
        <div class="request-wide-row" style="margin-top: 12px;">
          <!-- Данные заявки -->
          <div class="card request-panel request-panel--details">
            <b>Данные заявки</b>

            <div class="grid grid-2 request-details-grid" style="margin-top: 10px;">
              <template v-if="isBanquetBooking(it)">
                <div class="field">
                  <label>Вид помещения</label>
                  <div>{{ formatRoomType(it.payload?.room_type) }}</div>
                </div>

                <div class="field">
                  <label>Дата и время начала</label>
                  <div>{{ formatDate(it.payload?.start_at) }}</div>
                </div>

                <div class="field">
                  <label>Способ оплаты</label>
                  <div>{{ formatPaymentMethod(it.payload?.payment_method) }}</div>
                </div>
              </template>

              <div class="field" v-else>
                <label>Payload</label>
                <div style="opacity: 0.8;">(неизвестный тип заявки, показываю JSON)</div>
                <pre style="white-space: pre-wrap; margin: 8px 0 0;">{{ prettyPayload(it.payload) }}</pre>
              </div>
            </div>
          </div>

          <!-- Отзыв или форма отзыва -->
          <div class="card request-panel request-panel--feedback">
            <template v-if="it.feedback">
              <b>Ваш отзыв</b>

              <div style="margin-top: 10px;">
                <div>Оценка: ⭐ {{ it.feedback.rating }} / 5</div>
                <div v-if="it.feedback.comment" class="request-comment" style="margin-top: 8px;">
                  <b>Комментарий:</b>
                  <div style="opacity: 0.9;">{{ it.feedback.comment }}</div>
                </div>
                <div v-else style="margin-top: 8px; opacity: 0.8;">
                  Комментария нет.
                </div>
              </div>
            </template>

            <template v-else>
              <b>Оставить отзыв</b>

              <div class="grid" style="margin-top: 10px; gap: 12px;">
                <div class="field">
                  <label>Оценка (0–5)</label>
                  <input
                    type="number"
                    min="0"
                    max="5"
                    step="1"
                    v-model.number="rate[it.id]"
                  />
                </div>

                <div class="field">
                  <label>Комментарий</label>
                  <input v-model="comment[it.id]" />
                </div>
              </div>

              <div v-if="rateErr[it.id]" class="err" style="margin-top: 8px;">
                {{ rateErr[it.id] }}
              </div>

              <div v-if="rateOk[it.id]" style="margin-top: 8px; color: #16a34a;">
                OK ✅
              </div>

              <button
                class="btn"
                style="margin-top: 10px;"
                :disabled="!ratingIsValid(it.id)"
                @click="sendRate(it.id)"
              >
                Отправить
              </button>
            </template>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.request-wide-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
  align-items: stretch;
}

@media (max-width: 900px) {
  .request-wide-row {
    grid-template-columns: 1fr;
  }
}

.request-panel {
  padding: 16px;
  border-radius: var(--r-lg);
}

.request-panel--details {
  background: rgba(254, 237, 208, 0.55); /* кремовый */
}

.request-panel--feedback {
  background: rgba(255, 218, 185, 0.55); /* розово-золотистый */
}

.request-details-grid {
  gap: 12px;
}

.request-comment {
  white-space: pre-wrap;
  word-break: break-word;
}
</style>

<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";
import {
  formatStatus,
  formatRoomType,
  formatPaymentMethod,
  formatDate,
} from "@/utils/formatters";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const newStatus = ref({});
const statusErr = ref({});
const statusOk = ref({});

function isBanquetBooking(it) {
  return it?.type === "banquet_hall_booking";
}

function getRoomType(payload) {
  return payload?.room_type ?? payload?.room ?? payload?.place_type ?? null;
}
function getStartDate(payload) {
  return payload?.start_at ?? payload?.start_time ?? payload?.start ?? null;
}
function getPayment(payload) {
  return payload?.payment_method ?? payload?.payment ?? null;
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
    const res = await http.get("/api/admin/reqs/list");
    items.value = res.data.items || [];
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function setStatus(id) {
  statusErr.value[id] = "";
  statusOk.value[id] = false;

  const s = (newStatus.value[id] || "").trim();
  if (!s) {
    statusErr.value[id] = "Выберите статус";
    return;
  }

  try {
    await http.post(`/api/admin/reqs/${id}/status`, { status: s });
    statusOk.value[id] = true;
    await load();
  } catch (e) {
    statusErr.value[id] = apiErrorMessage(e);
  }
}

onMounted(load);
</script>

<template>
  <div class="card">
    <div class="row">
      <h2 style="margin: 0;">Панель администратора</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top: 10px;">{{ error }}</div>

    <div v-if="items.length === 0 && !loading" style="opacity: 0.8; margin-top: 12px;">
      Пока нет заявок.
    </div>

    <div class="grid" style="margin-top: 12px;">
      <div v-for="it in items" :key="it.id" class="card">
        <!-- Header заявки -->
        <div class="row">
          <div>
            <b>{{ isBanquetBooking(it) ? "Бронирование зала для банкета" : it.type }}</b>
            <div style="opacity: 0.8;">Пользователь: {{ it.user_login }} ({{ it.user_id }})</div>
            <div style="opacity: 0.8;">Статус: {{ formatStatus(it.status) }}</div>
          </div>
        </div>

        <!-- Wide row: Детали + Отзыв -->
        <div class="admin-wide-row" style="margin-top: 12px;">
          <!-- Детали заявки -->
          <div class="card admin-panel admin-panel--details">
            <b>Детали заявки</b>

            <div class="grid grid-2 admin-details-grid" style="margin-top: 10px;">
              <template v-if="isBanquetBooking(it)">
                <div class="field">
                  <label>Вид помещения</label>
                  <div>{{ formatRoomType(getRoomType(it.payload)) }}</div>
                </div>

                <div class="field">
                  <label>Дата и время начала</label>
                  <div>{{ formatDate(getStartDate(it.payload)) }}</div>
                </div>

                <div class="field">
                  <label>Способ оплаты</label>
                  <div>{{ formatPaymentMethod(getPayment(it.payload)) }}</div>
                </div>
              </template>

              <div class="field" v-else>
                <label>Payload</label>
                <div style="opacity: 0.8;">(неизвестный тип заявки, показываю JSON)</div>
                <pre style="white-space: pre-wrap; margin: 8px 0 0;">{{ prettyPayload(it.payload) }}</pre>
              </div>
            </div>
          </div>

          <!-- Отзыв (в одной колонке рядом) -->
          <div class="card admin-panel admin-panel--feedback">
            <b>Отзыв пользователя</b>

            <div v-if="it.feedback" style="margin-top: 10px;">
              <div><b>Оценка:</b> ⭐ {{ it.feedback.rating }} / 5</div>

              <div style="margin-top: 8px;">
                <b>Комментарий:</b>
                <div class="admin-comment">{{ it.feedback.comment || "—" }}</div>
              </div>
            </div>

            <div v-else style="margin-top: 10px; opacity: 0.8;">
              Отзыва пока нет.
            </div>
          </div>
        </div>

        <!-- Смена статуса -->
        <div class="grid grid-2" style="margin-top: 12px;">
          <div class="field">
            <label>Поменять статус</label>
            <select v-model="newStatus[it.id]">
              <option value="" disabled>— выберите —</option>
              <option value="new">Новая</option>
              <option value="in_progress">Банкет назначен</option>
              <option value="done">Банкет завершен</option>
            </select>
          </div>

          <div style="display: flex; align-items: end;">
            <button class="btn" @click="setStatus(it.id)">Сохранить</button>
          </div>
        </div>

        <div v-if="statusErr[it.id]" class="err" style="margin-top: 8px;">
          {{ statusErr[it.id] }}
        </div>
        <div v-if="statusOk[it.id]" style="margin-top: 8px; color: #16a34a;">
          Статус изменен ✅
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.admin-wide-row {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 12px;
  align-items: stretch;
}

@media (max-width: 900px) {
  .admin-wide-row {
    grid-template-columns: 1fr;
  }
}

.admin-panel {
  padding: 16px;
  border-radius: var(--r-lg);
}

.admin-panel--details {
  background: rgba(254, 237, 208, 0.55); /* кремовый полупрозрачный */
}

.admin-panel--feedback {
  background: rgba(255, 218, 185, 0.55); /* розово-золотистый полупрозрачный */
}

.admin-details-grid {
  gap: 12px;
}

.admin-comment {
  opacity: 0.9;
  white-space: pre-wrap;
  word-break: break-word;
  margin-top: 4px;
}
</style>

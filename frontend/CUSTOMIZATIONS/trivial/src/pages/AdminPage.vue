<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const newStatus = ref({});
const statusErr = ref({});
const statusOk = ref({});

function formatStatus(val) {
  const map = {
    new: "Новая",
    in_progress: "Идет обучение",
    done: "Обучение завершено",
  };
  return map[val] || val || "—";
}

function formatCourse(val) {
  const map = {
    qualification: "Курс повышения квалификации",
    retraining: "Курс переподготовки",
    labor_safety: "Курс по охране труда",
  };
  return map[val] || val || "—";
}

function formatPayment(val) {
  const map = {
    card: "Банковская карта",
    sbp: "СБП",
    invoice: "Счёт для юр. лица (безнал)",
    cash: "Наличные",
  };
  return map[val] || val || "—";
}

function formatDate(val) {
  if (!val) return "—";
  try {
    const d = new Date(val);
    if (Number.isNaN(d.getTime())) return String(val);
    return d.toLocaleString();
  } catch {
    return String(val);
  }
}

// достаем поля из payload максимально безопасно
function getCourseType(payload) {
  return payload?.course_type ?? payload?.course ?? payload?.type ?? null;
}
function getStartDate(payload) {
  return payload?.start_at ?? payload?.start_time ?? payload?.start ?? null;
}
function getPayment(payload) {
  return payload?.payment_method ?? payload?.payment ?? null;
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
    statusErr.value[id] = "status required";
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
      <h2 style="margin:0;">Панель администратора</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">{{ error }}</div>

    <div class="grid" style="margin-top:12px;">
      <div v-for="it in items" :key="it.id" class="card">
        <div class="row">
          <div>
            <b>Заявка на обучение</b>
            <div style="opacity:.8;">Пользователь: {{ it.user_login }} ({{ it.user_id }})</div>
            <div style="opacity:.8;">Статус: {{ formatStatus(it.status) }}</div>
          </div>
        </div>

        <!-- Детали заявки по ТЗ (вместо payload) -->
        <div class="card" style="margin-top:12px; background:#f8fafc;">
          <b>Детали заявки</b>

          <div class="grid grid-2" style="margin-top:10px;">
            <div class="field">
              <label>Вид курса</label>
              <div>{{ formatCourse(getCourseType(it.payload)) }}</div>
            </div>

            <div class="field">
              <label>Дата начала обучения</label>
              <div>{{ formatDate(getStartDate(it.payload)) }}</div>
            </div>

            <div class="field">
              <label>Способ оплаты</label>
              <div>{{ formatPayment(getPayment(it.payload)) }}</div>
            </div>
          </div>
        </div>

        <!-- Отзыв -->
        <div v-if="it.feedback" class="card" style="margin-top:12px; background:#fff7ed;">
          <b>Отзыв пользователя</b>

          <div style="margin-top:10px;">
            <div><b>Оценка:</b> ⭐ {{ it.feedback.rating }} / 5</div>

            <div style="margin-top:8px;">
              <b>Комментарий:</b>
              <div style="opacity:.9;">{{ it.feedback.comment || "—" }}</div>
            </div>
          </div>
        </div>

        <!-- Смена статуса -->
        <div class="grid grid-2" style="margin-top:12px;">
          <div class="field">
            <label>Поменять статус</label>
            <select v-model="newStatus[it.id]">
              <option value="" disabled>— выберите —</option>
              <option value="new">Новая</option>
              <option value="in_progress">Идет обучение</option>
              <option value="done">Обучение завершено</option>
            </select>
          </div>

          <div style="display:flex; align-items:end;">
            <button class="btn" @click="setStatus(it.id)">Сохранить</button>
          </div>
        </div>

        <div v-if="statusErr[it.id]" class="err" style="margin-top:8px;">{{ statusErr[it.id] }}</div>
        <div v-if="statusOk[it.id]" style="margin-top:8px; color:#16a34a;">Статус изменен ✅</div>
      </div>
    </div>
  </div>
</template>

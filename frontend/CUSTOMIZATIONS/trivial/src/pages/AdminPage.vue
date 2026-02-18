<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";

const items = ref([]);
const error = ref("");
const loading = ref(false);

const newStatus = ref({});
const statusErr = ref({});
const statusOk = ref({});

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
      <h2 style="margin:0;">Админка</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">{{ error }}</div>

    <div class="grid" style="margin-top:12px;">

      <div v-for="it in items" :key="it.id" class="card">

        <div class="row">
          <div>
            <b>{{ it.type }}</b>
            <div style="opacity:.8;">user: {{ it.user_login }} ({{ it.user_id }})</div>
            <div style="opacity:.8;">status: {{ it.status }}</div>
          </div>
        </div>

        <details style="margin-top:10px;">
          <summary style="cursor:pointer;">payload</summary>
          <pre style="white-space: pre-wrap;">{{ it.payload }}</pre>
        </details>

        <!-- Отзыв -->
        <div v-if="it.feedback" class="card" style="margin-top:12px; background:#fff7ed;">
          <b>Отзыв пользователя</b>

          <div style="margin-top:10px;">

            <div class="row">
              <div><b>Оценка:</b> {{ it.feedback.rating }} / 5</div>
            </div>

            <div style="margin-top:8px;">
              <b>Комментарий:</b>
              <div style="opacity:.9;">{{ it.feedback.comment || "—" }}</div>
            </div>

          </div>
        </div>

        <div class="grid grid-2" style="margin-top:12px;">
          <div class="field">
            <label>New status</label>
            <select v-model="newStatus[it.id]">
              <option value="" disabled>— выберите —</option>
              <option value="new">new</option>
              <option value="in_progress">in_progress</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
              <option value="done">done</option>
            </select>
          </div>
          <div style="display:flex; align-items:end;">
            <button class="btn" @click="setStatus(it.id)">Сохранить</button>
          </div>
        </div>

        <div v-if="statusErr[it.id]" class="err" style="margin-top:8px;">{{ statusErr[it.id] }}</div>
        <div v-if="statusOk[it.id]" style="margin-top:8px; color:#2da44e;">OK ✅</div>
      </div>
    </div>
  </div>
</template>

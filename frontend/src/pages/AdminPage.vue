<script setup>
import { onMounted, ref } from "vue";
import { http, apiErrorMessage } from "@/api/http";

const items = ref([]);
const error = ref(null);
const loading = ref(false);

const statusDraft = ref({});
const commentDraft = ref({});
const okMsg = ref({});
const errMsg = ref({});

async function load() {
  loading.value = true;
  error.value = null;
  try {
    const res = await http.get("/admin/requests");
    items.value = res.data.items || [];
    for (const it of items.value) {
      statusDraft.value[it.id] = it.status;
      commentDraft.value[it.id] = it.admin_comment || "";
    }
  } catch (e) {
    error.value = apiErrorMessage(e);
  } finally {
    loading.value = false;
  }
}

async function save(it) {
  okMsg.value[it.id] = false;
  errMsg.value[it.id] = "";
  try {
    await http.patch(`/admin/requests/${it.id}/status`, {
      status: statusDraft.value[it.id],
      admin_comment: commentDraft.value[it.id] || null,
    });
    okMsg.value[it.id] = true;
    await load();
  } catch (e) {
    errMsg.value[it.id] = apiErrorMessage(e);
  }
}

onMounted(load);
</script>

<template>
  <div class="card">
    <div class="row">
      <h2 style="margin:0;">Панель администратора</h2>
      <button class="btn secondary" @click="load" :disabled="loading">
        {{ loading ? "Обновление..." : "Обновить" }}
      </button>
    </div>

    <div v-if="error" class="err" style="margin-top:10px;">{{ error }}</div>

    <div class="grid" style="margin-top:12px;">
      <div v-for="it in items" :key="it.id" class="card">
        <div class="row">
          <div>
            <b>{{ it.type }}</b>
            <div style="opacity:0.8; font-size: 14px;">Пользователь: {{ it.user_login }}</div>
            <div style="opacity:0.8; font-size: 14px;">ID: {{ it.id }}</div>
          </div>
          <div class="card" style="padding:6px 10px;">Текущий статус: <b>{{ it.status }}</b></div>
        </div>

        <pre style="white-space: pre-wrap; font-size: 13px; margin-top: 10px;">{{ it.payload }}</pre>

        <div class="grid grid-2" style="margin-top:12px;">
          <div class="field">
            <label>Статус</label>
            <select v-model="statusDraft[it.id]">
              <option value="new">new</option>
              <option value="in_progress">in_progress</option>
              <option value="approved">approved</option>
              <option value="rejected">rejected</option>
              <option value="done">done</option>
            </select>
          </div>
          <div class="field">
            <label>Комментарий администратора</label>
            <input v-model="commentDraft[it.id]" placeholder="Комментарий" />
          </div>
        </div>

        <div v-if="errMsg[it.id]" class="err" style="margin-top:8px;">{{ errMsg[it.id] }}</div>
        <div v-if="okMsg[it.id]" style="margin-top:8px; color:#7bff9b;">Сохранено ✅</div>

        <button class="btn" style="margin-top:10px;" @click="save(it)">Сохранить</button>
      </div>
    </div>
  </div>
</template>

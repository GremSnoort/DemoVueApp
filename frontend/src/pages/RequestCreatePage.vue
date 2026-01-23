<script setup>
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";
import { http, apiErrorMessage } from "@/api/http";
import { domain } from "@/domain/domain.config";
import { buildDefaultForm, getTypeDef, validateForm } from "@/domain/domain.utils";

const router = useRouter();

const type = ref(domain.requestTypes[0]?.type || "");
const form = ref(buildDefaultForm(type.value));

const error = ref(null);
const loading = ref(false);

const typeDef = computed(() => getTypeDef(type.value));

function pretty(v) {
  try { return JSON.stringify(v, null, 2); } catch { return String(v); }
}

watch(type, (newType) => {
  form.value = buildDefaultForm(newType);
  error.value = null;
});

async function onSubmit() {
  error.value = null;

  if (!type.value) {
    error.value = "Выберите тип заявки";
    return;
  }

  const vErr = validateForm(type.value, form.value);
  if (vErr) {
    error.value = vErr;
    return;
  }

  loading.value = true;
  try {
    await http.post("/requests", {
      type: type.value,
      payload: form.value,
    });
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
        <select v-model="type">
          <option value="" disabled>— выберите тип —</option>
          <option v-for="t in domain.requestTypes" :key="t.type" :value="t.type">
            {{ t.title }}
          </option>
        </select>
        <div v-if="typeDef?.description" style="opacity:0.8; font-size: 14px;">
          {{ typeDef.description }}
        </div>
      </div>

      <!-- Динамические поля -->
      <div v-if="typeDef" class="grid grid-2">
        <div v-for="f in typeDef.fields" :key="f.key" class="field" :style="f.kind==='textarea' ? 'grid-column: 1 / -1;' : ''">
          <label>
            {{ f.label }}
            <span v-if="f.required" style="color:#ff7b7b;"> *</span>
          </label>

          <input
            v-if="f.kind==='text'"
            v-model="form[f.key]"
            :placeholder="f.placeholder || ''"
          />

          <input
            v-else-if="f.kind==='date'"
            type="date"
            v-model="form[f.key]"
          />

          <textarea
            v-else-if="f.kind==='textarea'"
            rows="4"
            v-model="form[f.key]"
            :placeholder="f.placeholder || ''"
          />

          <select
            v-else-if="f.kind==='select'"
            v-model="form[f.key]"
          >
            <option value="" disabled>— выберите —</option>
            <option v-for="o in (f.options || [])" :key="o.value" :value="o.value">
              {{ o.label }}
            </option>
          </select>

          <label v-else-if="f.kind==='checkbox'" style="display:flex; gap:10px; align-items:center;">
            <input type="checkbox" v-model="form[f.key]" />
            <span style="opacity:0.9;">{{ f.placeholder || "Да/Нет" }}</span>
          </label>

          <div v-if="f.hint" style="opacity:0.75; font-size: 13px;">{{ f.hint }}</div>
        </div>
      </div>

      <button class="btn" :disabled="loading" @click="onSubmit">
        {{ loading ? "Отправка..." : "Отправить" }}
      </button>

      <details class="card" style="opacity:0.9;">
        <summary>Payload, который уйдёт на backend (для отладки)</summary>
        <pre style="white-space: pre-wrap; font-size: 13px; margin: 10px 0 0;">{{ pretty(form) }}</pre>
      </details>
    </div>
  </div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import TopSlider from "@/components/TopSlider.vue";
import { authStore } from "@/auth/auth.store";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const type = ref("course_request");

// Поля (по ТЗ)
const courseType = ref("qualification");
const startAt = ref("");
const paymentMethod = ref("");

const error = ref("");
const loading = ref(false);

function validate() {
  if (!courseType.value) return "Выберите вид курса";
  if (!startAt.value) return "Укажите дату и время начала";
  if (!paymentMethod.value) return "Выберите способ оплаты";
  return "";
}

async function submit() {
  error.value = "";
  const v = validate();
  if (v) {
    error.value = v;
    return;
  }

  loading.value = true;
  try {
    await http.post("/api/user/reqs/create", {
      type: type.value,
      payload: {
        course_type: courseType.value,
        start_at: startAt.value, // строка из input datetime-local
        payment_method: paymentMethod.value,
      },
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
  <TopSlider v-if="authStore.isAuthed()" />

  <div class="card">
    <h2>Оформление заявки на курс</h2>

    <div v-if="error" class="err">{{ error }}</div>

    <div class="grid">
      <div class="field">
        <label>Вид курса</label>
        <select v-model="courseType">
          <option value="qualification">Курс повышения квалификации</option>
          <option value="retraining">Курс переподготовки</option>
          <option value="labor_safety">Курс по охране труда</option>
        </select>
      </div>

      <div class="field">
        <label>Предпочтительное время старта занятий</label>
        <input type="datetime-local" v-model="startAt" />
      </div>

      <div class="field">
        <label>Способ оплаты</label>
        <select v-model="paymentMethod">
          <option value="" disabled>— выберите способ оплаты —</option>
          <option value="card">Банковская карта</option>
          <option value="sbp">СБП</option>
          <option value="invoice">Счёт для юр. лица (безнал)</option>
          <option value="cash">Наличные</option>
        </select>
      </div>

      <button class="btn" :disabled="loading" @click="submit">
        {{ loading ? "..." : "Отправить заявку" }}
      </button>
    </div>
  </div>
</template>

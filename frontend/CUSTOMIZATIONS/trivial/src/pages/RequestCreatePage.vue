<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import TopSlider from "@/components/TopSlider.vue";
import { authStore } from "@/auth/auth.store";
import { http, apiErrorMessage } from "@/api/http";

const router = useRouter();

const type = "banquet_hall_booking";

// Опции по ТЗ
const ROOM_TYPES = [
  { value: "hall", label: "Зал" },
  { value: "restaurant", label: "Ресторан" },
  { value: "summer_veranda", label: "Летняя веранда" },
  { value: "closed_veranda", label: "Закрытая веранда" },
];

const PAYMENT_METHODS = [
  { value: "card", label: "Банковская карта" },
  { value: "sbp", label: "СБП" },
  { value: "invoice", label: "Счёт для юр. лица (безнал)" },
  { value: "cash", label: "Наличные" },
];

const roomType = ref("");
const startAt = ref("");
const paymentMethod = ref("");

const error = ref("");
const loading = ref(false);

const minDateTimeLocal = computed(() => {
  const d = new Date();
  const pad = (n) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(
    d.getHours()
  )}:${pad(d.getMinutes())}`;
});

const validationError = computed(() => {
  if (!roomType.value) return "Выберите вид помещения";
  if (!startAt.value) return "Укажите дату и время начала";
  if (!paymentMethod.value) return "Выберите способ оплаты";
  return "";
});

const canSubmit = computed(() => !loading.value && !validationError.value);

async function submit() {
  error.value = "";
  if (validationError.value) {
    error.value = validationError.value;
    return;
  }

  loading.value = true;
  try {
    await http.post("/api/user/reqs/create", {
      type,
      payload: {
        room_type: roomType.value,
        start_at: startAt.value,
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
    <h2>Заявка на бронирование зала для банкета</h2>

    <div v-if="error" class="err">{{ error }}</div>

    <form class="grid" @submit.prevent="submit">
      <div class="field">
        <label>Вид помещения</label>
        <select v-model="roomType">
          <option value="" disabled>— выберите вид помещения —</option>
          <option v-for="o in ROOM_TYPES" :key="o.value" :value="o.value">
            {{ o.label }}
          </option>
        </select>
      </div>

      <div class="field">
        <label>Дата и время начала</label>
        <input
          type="datetime-local"
          v-model="startAt"
          :min="minDateTimeLocal"
        />
      </div>

      <div class="field">
        <label>Способ оплаты</label>
        <select v-model="paymentMethod">
          <option value="" disabled>— выберите способ оплаты —</option>
          <option v-for="o in PAYMENT_METHODS" :key="o.value" :value="o.value">
            {{ o.label }}
          </option>
        </select>
      </div>

      <button class="btn" type="submit" :disabled="!canSubmit">
        {{ loading ? "..." : "Отправить заявку" }}
      </button>
    </form>
  </div>
</template>

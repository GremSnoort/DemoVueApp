// src/utils/formatters.js

// ===== STATUS =====
export function formatStatus(val) {
  const map = {
    new: "Новая",
    in_progress: "Банкет назначен",
    done: "Банкет завершен",
  };
  return map[val] || val || "—";
}

// ===== ROOM TYPE =====
export function formatRoomType(v) {
  const map = {
    hall: "Зал",
    restaurant: "Ресторан",
    summer_veranda: "Летняя веранда",
    closed_veranda: "Закрытая веранда",
  };
  return map[v] || v || "—";
}

// ===== PAYMENT =====
export function formatPaymentMethod(v) {
  const map = {
    card: "Банковская карта",
    sbp: "СБП",
    invoice: "Счёт для юр. лица (безнал)",
    cash: "Наличные",
  };
  return map[v] || v || "—";
}

// ===== DATE =====
export function formatDate(val) {
  if (!val) return "—";
  try {
    const d = new Date(val);
    if (Number.isNaN(d.getTime())) return String(val);

    return d.toLocaleString("ru-RU", {
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return String(val);
  }
}

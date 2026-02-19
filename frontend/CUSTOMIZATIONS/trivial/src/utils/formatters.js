// src/utils/formatters.js

// ===== STATUS =====
export function formatStatus(val) {
  const map = {
    new: "Новая",
    in_progress: "Идет обучение",
    done: "Обучение завершено",
  };
  return map[val] || val || "—";
}

// ===== COURSE =====
export function formatCourse(val) {
  const map = {
    qualification: "Курс повышения квалификации",
    retraining: "Курс переподготовки",
    labor_safety: "Курс по охране труда",
  };
  return map[val] || val || "—";
}

// ===== PAYMENT =====
export function formatPayment(val) {
  const map = {
    card: "Банковская карта",
    sbp: "СБП",
    invoice: "Счёт для юр. лица (безнал)",
    cash: "Наличные",
  };
  return map[val] || val || "—";
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

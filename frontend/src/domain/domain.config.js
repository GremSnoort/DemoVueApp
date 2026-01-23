// src/domain/domain.config.js
// Меняешь только этот файл — и получаешь другую предметную область.

export const domain = {
  appTitle: "DemoVueApp",
  // Список типов заявок (type), которые уйдут в backend
  requestTypes: [
    {
      type: "service_visit",
      title: "Запись в автосервис",
      description: "Создать заявку на посещение",
      fields: [
        { key: "car_brand", label: "Марка авто", kind: "text", required: true, placeholder: "Toyota" },
        { key: "car_model", label: "Модель", kind: "text", required: true, placeholder: "Camry" },
        { key: "date", label: "Дата визита", kind: "date", required: true },
        { key: "problem", label: "Описание проблемы", kind: "textarea", required: true, placeholder: "Опишите проблему" },
        { key: "urgent", label: "Срочно", kind: "checkbox", required: false },
      ],
      // Как красиво показывать карточку заявки в списке
      summary(payload) {
        const brand = payload?.car_brand || "—";
        const model = payload?.car_model || "—";
        const date = payload?.date || "—";
        return `${brand} ${model} • ${date}`;
      },
    },

    // Пример второго типа — можешь удалить/заменить
    {
      type: "course_enroll",
      title: "Запись на курс",
      description: "Заявка на обучение",
      fields: [
        { key: "course_title", label: "Название курса", kind: "text", required: true, placeholder: "Python для начинающих" },
        { key: "format", label: "Формат", kind: "select", required: true, options: [
          { value: "online", label: "Онлайн" },
          { value: "offline", label: "Оффлайн" },
        ]},
        { key: "comment", label: "Комментарий", kind: "textarea", required: false },
      ],
      summary(payload) {
        return `${payload?.course_title || "—"} • ${payload?.format || "—"}`;
      },
    },
  ],

  // Список допустимых статусов (для админки)
  statuses: [
    { value: "new", label: "new" },
    { value: "in_progress", label: "in_progress" },
    { value: "approved", label: "approved" },
    { value: "rejected", label: "rejected" },
    { value: "done", label: "done" },
  ],
};

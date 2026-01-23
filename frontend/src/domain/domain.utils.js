// src/domain/domain.utils.js
import { domain } from "./domain.config";

export function getTypeDef(type) {
  return domain.requestTypes.find((x) => x.type === type) || null;
}

export function getTypeTitle(type) {
  return getTypeDef(type)?.title || type || "request";
}

export function buildDefaultForm(type) {
  const def = getTypeDef(type);
  const form = {};
  if (!def) return form;

  for (const f of def.fields || []) {
    if (f.kind === "checkbox") form[f.key] = false;
    else form[f.key] = f.default ?? "";
  }
  return form;
}

export function validateForm(type, form) {
  const def = getTypeDef(type);
  if (!def) return null;

  for (const f of def.fields || []) {
    if (!f.required) continue;

    const v = form[f.key];
    if (f.kind === "checkbox") {
      // checkbox required редко нужен — оставим как есть
      continue;
    }
    if (v === null || v === undefined || String(v).trim() === "") {
      return `Поле "${f.label}" обязательно`;
    }
  }
  return null;
}

export function makeSummary(type, payload) {
  const def = getTypeDef(type);
  if (def?.summary) {
    try {
      return def.summary(payload);
    } catch {
      return "";
    }
  }
  return "";
}

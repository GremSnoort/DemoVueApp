const KEY = "demo_theme";

export function getTheme() {
  return localStorage.getItem(KEY) || null;
}

export function applyTheme(name) {
  const link = document.getElementById("theme");
  if (!link) return;
  link.href = `/themes/${name}.css`;
}

export function setTheme(name) {
  localStorage.setItem(KEY, name);
  applyTheme(name);
}

export function initTheme(fallback = "theme-light") {
  const saved = getTheme() || fallback;
  applyTheme(saved);
  return saved;
}


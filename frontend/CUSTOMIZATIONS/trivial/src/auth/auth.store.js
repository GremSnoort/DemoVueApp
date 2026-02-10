import { reactive } from "vue";

const KEY = "demo_auth";

function load() {
  try {
    return JSON.parse(localStorage.getItem(KEY) || "null");
  } catch {
    return null;
  }
}

const saved = load();

export const authStore = reactive({
  token: saved?.token || "",
  user: saved?.user || null,

  isAuthed() {
    return !!this.token;
  },
  isAdmin() {
    return this.user?.role === "admin";
  },
  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem(KEY, JSON.stringify({ token, user }));
  },
  logout() {
    this.token = "";
    this.user = null;
    localStorage.removeItem(KEY);
  },
});

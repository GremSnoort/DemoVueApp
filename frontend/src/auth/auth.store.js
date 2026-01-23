import { reactive } from "vue";

const TOKEN_KEY = "demo_jwt";
const USER_KEY = "demo_user";

function loadUser() {
  const raw = localStorage.getItem(USER_KEY);
  return raw ? JSON.parse(raw) : null;
}

export const authStore = reactive({
  token: localStorage.getItem(TOKEN_KEY) || null,
  user: loadUser(), // {id, login, full_name, role} | null

  setAuth(token, user) {
    this.token = token;
    this.user = user;
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },

  logout() {
    this.token = null;
    this.user = null;
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  },

  isAuthed() {
    return !!this.token;
  },

  isAdmin() {
    return this.user?.role === "admin";
  },
});

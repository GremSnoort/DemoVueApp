const TOKEN_KEY = "demo_jwt";
const USER_KEY = "demo_user";

export const auth = {
  getToken() {
    return localStorage.getItem(TOKEN_KEY);
  },
  setToken(token) {
    localStorage.setItem(TOKEN_KEY, token);
  },
  clearToken() {
    localStorage.removeItem(TOKEN_KEY);
  },

  getUser() {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? JSON.parse(raw) : null;
  },
  setUser(user) {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clearUser() {
    localStorage.removeItem(USER_KEY);
  },

  logout() {
    this.clearToken();
    this.clearUser();
  },

  isAuthed() {
    return !!this.getToken();
  },
  isAdmin() {
    const u = this.getUser();
    return u && u.role === "admin";
  },
};

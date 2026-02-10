import axios from "axios";
import { authStore } from "@/auth/auth.store";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

export const http = axios.create({
  baseURL: API_BASE,
});

http.interceptors.request.use((config) => {
  const token = authStore.token;
  if (token) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export function apiErrorMessage(e) {
  const d = e?.response?.data;
  return d?.detail?.error || d?.error || e?.message || "api error";
}

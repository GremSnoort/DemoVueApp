import axios from "axios";
import { auth } from "@/auth/auth";

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 15000,
});

http.interceptors.request.use((config) => {
  const token = auth.getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

http.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) auth.logout();
    return Promise.reject(err);
  }
);

export function apiErrorMessage(e) {
  return e?.response?.data?.error || e?.message || "Unknown error";
}

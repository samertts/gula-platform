import axios from "axios";

const api = axios.create({
  baseURL: "/api",
  timeout: 15000,
  headers: { "Content-Type": "application/json" },
});

/* attach token from localStorage */
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("nhop_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

/* handle 401 → redirect to login */
api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("nhop_token");
      localStorage.removeItem("nhop_user");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;

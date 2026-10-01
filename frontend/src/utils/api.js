import axios from "axios";

// Create an Axios instance
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Real stats computed by the backend from stored scans
export const getDashboard = async () => (await api.get("/scanner/dashboard-stats")).data;

export const getModelMetrics = async () => (await api.get("/model/metrics")).data;

export const getIocs = async () => (await api.get("/scanner/iocs")).data;

// Turn an Axios error into a readable string (FastAPI 422 errors return a list of objects)
export const errorMessage = (err, fallback) => {
  const detail = err?.response?.data?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail.length) {
    return detail.map((d) => `${(d.loc || []).slice(-1)[0] || "input"}: ${d.msg}`).join("; ");
  }
  return fallback;
};

export default api;

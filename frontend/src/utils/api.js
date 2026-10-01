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

export default api;

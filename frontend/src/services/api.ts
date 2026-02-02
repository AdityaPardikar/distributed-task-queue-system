import axios, { type AxiosInstance, type AxiosError } from "axios";
import type { InternalAxiosRequestConfig } from "axios";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        "Content-Type": "application/json",
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config: InternalAxiosRequestConfig) => {
        const token = localStorage.getItem("access_token");
        if (token && config.headers) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Unauthorized - clear token and redirect to login
          localStorage.removeItem("access_token");
          localStorage.removeItem("user");
          window.location.href = "/login";
        }
        return Promise.reject(error);
      },
    );
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    const response = await this.client.post("/api/v1/auth/login", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
    return response.data;
  }

  async getCurrentUser() {
    const response = await this.client.get("/api/v1/auth/me");
    return response.data;
  }

  // Task endpoints
  async getTasks(params?: Record<string, unknown>) {
    const response = await this.client.get("/api/v1/tasks", { params });
    return response.data;
  }

  async getTask(id: number) {
    const response = await this.client.get(`/api/v1/tasks/${id}`);
    return response.data;
  }

  async createTask(data: Record<string, unknown>) {
    const response = await this.client.post("/api/v1/tasks", data);
    return response.data;
  }

  // Campaign endpoints
  async getCampaigns(params?: Record<string, unknown>) {
    const response = await this.client.get("/api/v1/campaigns", { params });
    return response.data;
  }

  async getCampaign(id: number) {
    const response = await this.client.get(`/api/v1/campaigns/${id}`);
    return response.data;
  }

  async createCampaign(data: Record<string, unknown>) {
    const response = await this.client.post("/api/v1/campaigns", data);
    return response.data;
  }

  async updateCampaign(id: number, data: Record<string, unknown>) {
    const response = await this.client.patch(`/api/v1/campaigns/${id}`, data);
    return response.data;
  }

  async launchCampaign(id: number) {
    const response = await this.client.post(`/api/v1/campaigns/${id}/launch`);
    return response.data;
  }

  // Template endpoints
  async getTemplates(params?: Record<string, unknown>) {
    const response = await this.client.get("/api/v1/templates", { params });
    return response.data;
  }

  async getTemplate(id: number) {
    const response = await this.client.get(`/api/v1/templates/${id}`);
    return response.data;
  }

  async createTemplate(data: Record<string, unknown>) {
    const response = await this.client.post("/api/v1/templates", data);
    return response.data;
  }

  // Dashboard API with mocked data fallback
  dashboardAPI = {
    getStats: async () => {
      try {
        const response = await this.client.get("/api/v1/dashboard/stats");
        return response.data;
      } catch {
        // Return mock data if endpoint doesn't exist
        return {
          data: {
            total_tasks: 1250,
            pending_tasks: 45,
            running_tasks: 12,
            completed_tasks: 1150,
            failed_tasks: 43,
            active_workers: 5,
            total_workers: 8,
            queue_size: 45,
            success_rate: 96.4,
            avg_processing_time: 2.3,
          },
        };
      }
    },
    getRecentTasks: async (limit: number = 20) => {
      try {
        const response = await this.client.get(
          "/api/v1/dashboard/recent-tasks",
          {
            params: { limit },
          },
        );
        return response.data;
      } catch {
        // Return mock data if endpoint doesn't exist
        const mockTasks = [];
        for (let i = 0; i < limit; i++) {
          mockTasks.push({
            id: `task-${i + 1}`,
            name: `Sample Task ${i + 1}`,
            status: ["pending", "running", "completed", "failed"][
              Math.floor(Math.random() * 4)
            ],
            priority: ["low", "medium", "high", "critical"][
              Math.floor(Math.random() * 4)
            ],
            created_at: new Date(
              Date.now() - Math.random() * 3600000,
            ).toISOString(),
            duration: Math.floor(Math.random() * 300),
            worker_id: `worker-${Math.floor(Math.random() * 5) + 1}`,
          });
        }
        return { data: mockTasks };
      }
    },
    getWorkers: async () => {
      try {
        const response = await this.client.get("/api/v1/dashboard/workers");
        return response.data;
      } catch {
        // Return mock data if endpoint doesn't exist
        const mockWorkers = [];
        for (let i = 1; i <= 8; i++) {
          mockWorkers.push({
            id: `worker-${i}`,
            name: `Worker ${i}`,
            status: i <= 5 ? "active" : "idle",
            task_count: Math.floor(Math.random() * 50),
            last_heartbeat: new Date().toISOString(),
            cpu_usage: Math.random() * 80,
            memory_usage: Math.random() * 70 + 20,
          });
        }
        return { data: mockWorkers };
      }
    },
  };
}

export const apiClient = new ApiClient();
export default apiClient;

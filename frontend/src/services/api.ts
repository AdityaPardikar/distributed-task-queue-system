import axios, {
  AxiosInstance,
  AxiosError,
  InternalAxiosRequestConfig,
} from "axios";

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
  async getTasks(params?: Record<string, any>) {
    const response = await this.client.get("/api/v1/tasks", { params });
    return response.data;
  }

  async getTask(id: number) {
    const response = await this.client.get(`/api/v1/tasks/${id}`);
    return response.data;
  }

  async createTask(data: Record<string, any>) {
    const response = await this.client.post("/api/v1/tasks", data);
    return response.data;
  }

  // Campaign endpoints
  async getCampaigns(params?: Record<string, any>) {
    const response = await this.client.get("/api/v1/campaigns", { params });
    return response.data;
  }

  async getCampaign(id: number) {
    const response = await this.client.get(`/api/v1/campaigns/${id}`);
    return response.data;
  }

  async createCampaign(data: Record<string, any>) {
    const response = await this.client.post("/api/v1/campaigns", data);
    return response.data;
  }

  async updateCampaign(id: number, data: Record<string, any>) {
    const response = await this.client.patch(`/api/v1/campaigns/${id}`, data);
    return response.data;
  }

  async launchCampaign(id: number) {
    const response = await this.client.post(`/api/v1/campaigns/${id}/launch`);
    return response.data;
  }

  // Template endpoints
  async getTemplates(params?: Record<string, any>) {
    const response = await this.client.get("/api/v1/templates", { params });
    return response.data;
  }

  async getTemplate(id: number) {
    const response = await this.client.get(`/api/v1/templates/${id}`);
    return response.data;
  }

  async createTemplate(data: Record<string, any>) {
    const response = await this.client.post("/api/v1/templates", data);
    return response.data;
  }
}

export const apiClient = new ApiClient();
export default apiClient;

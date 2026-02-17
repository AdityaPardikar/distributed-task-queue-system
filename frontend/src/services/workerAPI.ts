/**
 * Worker API service — wraps all /api/v1/workers/* endpoints.
 */

import axios from "axios";
import type {
  Worker,
  WorkerListResponse,
  WorkerTasksResponse,
  WorkerRegisterParams,
} from "../types/worker";

const API_BASE_URL = import.meta.env.VITE_API_URL || "";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

// Attach auth token
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const workerAPI = {
  /** List workers with pagination and optional status filter. */
  list: async (
    page = 1,
    pageSize = 20,
    status?: string,
  ): Promise<WorkerListResponse> => {
    const params: Record<string, unknown> = { page, page_size: pageSize };
    if (status) params.worker_status = status;
    const res = await client.get<WorkerListResponse>("/api/v1/workers", {
      params,
    });
    return res.data;
  },

  /** Get a single worker by ID. */
  get: async (id: string): Promise<Worker> => {
    const res = await client.get<Worker>(`/api/v1/workers/${id}`);
    return res.data;
  },

  /** Register a new worker. */
  register: async (params: WorkerRegisterParams): Promise<Worker> => {
    const res = await client.post<Worker>("/api/v1/workers", null, {
      params: { hostname: params.hostname, capacity: params.capacity },
    });
    return res.data;
  },

  /** Send heartbeat for a worker. */
  heartbeat: async (
    id: string,
    currentLoad: number,
    status = "ACTIVE",
  ): Promise<Worker> => {
    const res = await client.post<Worker>(
      `/api/v1/workers/${id}/heartbeat`,
      null,
      { params: { current_load: currentLoad, worker_status: status } },
    );
    return res.data;
  },

  /** Update worker status (ACTIVE / DRAINING / OFFLINE). */
  updateStatus: async (id: string, newStatus: string): Promise<Worker> => {
    const res = await client.patch<Worker>(
      `/api/v1/workers/${id}/status`,
      null,
      {
        params: { new_status: newStatus },
      },
    );
    return res.data;
  },

  /** Get tasks assigned to a worker. */
  getTasks: async (id: string): Promise<WorkerTasksResponse> => {
    const res = await client.get<WorkerTasksResponse>(
      `/api/v1/workers/${id}/tasks`,
    );
    return res.data;
  },

  /** Pause a worker. */
  pause: async (id: string): Promise<Worker> => {
    const res = await client.post<Worker>(`/api/v1/workers/${id}/pause`);
    return res.data;
  },

  /** Resume a worker. */
  resume: async (id: string): Promise<Worker> => {
    const res = await client.post<Worker>(`/api/v1/workers/${id}/resume`);
    return res.data;
  },

  /** Drain a worker (finish current tasks, stop accepting new ones). */
  drain: async (id: string): Promise<Worker> => {
    const res = await client.post<Worker>(`/api/v1/workers/${id}/drain`);
    return res.data;
  },

  /** Remove / deregister a worker. */
  remove: async (id: string): Promise<void> => {
    await client.delete(`/api/v1/workers/${id}`);
  },
};

export default workerAPI;

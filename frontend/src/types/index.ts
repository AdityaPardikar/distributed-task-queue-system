export interface User {
  id: number;
  email: string;
  username: string;
  is_active: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Task {
  id: number;
  task_type: string;
  payload: Record<string, any>;
  status: "pending" | "running" | "completed" | "failed" | "cancelled";
  priority: number;
  created_at: string;
  updated_at: string;
}

export interface Campaign {
  id: number;
  name: string;
  description?: string;
  status: "draft" | "scheduled" | "running" | "paused" | "completed" | "failed";
  template_id?: number;
  created_at: string;
  updated_at: string;
}

export interface EmailTemplate {
  id: number;
  name: string;
  subject: string;
  body: string;
  variables: string[];
  version: number;
  created_at: string;
  updated_at: string;
}

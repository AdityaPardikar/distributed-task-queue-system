export interface User {
  user_id: string;
  username: string;
  email: string;
  full_name?: string;
  role: "admin" | "operator" | "viewer";
  is_active: boolean;
  is_superuser: boolean;
  created_at: string;
  last_login?: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role?: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface Task {
  id: number;
  task_type: string;
  payload: Record<string, unknown>;
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

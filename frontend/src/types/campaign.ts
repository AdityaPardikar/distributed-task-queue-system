/**
 * Campaign and Email Template types
 */

export interface Campaign {
  id: number;
  name: string;
  description: string;
  status: "draft" | "scheduled" | "running" | "paused" | "completed" | "failed";
  template_id: number;
  rate_limit: number;
  created_at: string;
  updated_at: string;
  total_tasks?: number;
  completed_tasks?: number;
  failed_tasks?: number;
}

export interface CampaignCreate {
  name: string;
  description: string;
  template_id: number;
  rate_limit: number;
}

export interface CampaignUpdate {
  name?: string;
  description?: string;
  status?:
    | "draft"
    | "scheduled"
    | "running"
    | "paused"
    | "completed"
    | "failed";
  rate_limit?: number;
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

export interface EmailTemplateCreate {
  name: string;
  subject: string;
  body: string;
}

export interface EmailTemplateUpdate {
  name?: string;
  subject?: string;
  body?: string;
}

export interface EmailRecipient {
  id: number;
  email: string;
  variables: Record<string, string>;
  status: "pending" | "sent" | "failed" | "bounced";
  created_at: string;
}

export interface EmailRecipientCreate {
  email: string;
  variables: Record<string, string>;
}

export interface CampaignLaunchRequest {
  template_id?: number;
}

export interface CampaignStatus {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  pending_tasks: number;
}

export interface TemplatePreview {
  subject: string;
  body: string;
}

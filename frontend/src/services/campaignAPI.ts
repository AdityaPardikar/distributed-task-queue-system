/**
 * Campaign API service
 */

import axios from "axios";
import type {
  Campaign,
  CampaignCreate,
  CampaignUpdate,
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplateUpdate,
  EmailRecipient,
  EmailRecipientCreate,
  CampaignLaunchRequest,
  CampaignStatus,
  TemplatePreview,
} from "../types/campaign";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

const client = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
});

// Add auth token to requests
client.interceptors.request.use((config) => {
  const token = localStorage.getItem("access_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Campaign endpoints
export const campaignAPI = {
  // Get all campaigns
  list: async (skip: number = 0, limit: number = 10) => {
    return client.get<{ data: Campaign[]; total: number }>(
      "/api/v1/campaigns",
      {
        params: { skip, limit },
      },
    );
  },

  // Get campaign by ID
  get: async (id: number) => {
    return client.get<Campaign>(`/api/v1/campaigns/${id}`);
  },

  // Create campaign
  create: async (data: CampaignCreate) => {
    return client.post<Campaign>("/api/v1/campaigns", data);
  },

  // Update campaign
  update: async (id: number, data: CampaignUpdate) => {
    return client.patch<Campaign>(`/api/v1/campaigns/${id}`, data);
  },

  // Delete campaign
  delete: async (id: number) => {
    return client.delete(`/api/v1/campaigns/${id}`);
  },

  // Get campaign status
  getStatus: async (id: number) => {
    return client.get<CampaignStatus>(`/api/v1/campaigns/${id}/status`);
  },

  // Launch campaign
  launch: async (id: number, data?: CampaignLaunchRequest) => {
    return client.post(`/api/v1/campaigns/${id}/launch`, data || {});
  },

  // Pause campaign
  pause: async (id: number) => {
    return client.patch<Campaign>(`/api/v1/campaigns/${id}`, {
      status: "paused",
    });
  },

  // Resume campaign
  resume: async (id: number) => {
    return client.patch<Campaign>(`/api/v1/campaigns/${id}`, {
      status: "running",
    });
  },
};

// Email Template endpoints
export const templateAPI = {
  // Get all templates
  list: async (campaign_id?: number, skip: number = 0, limit: number = 10) => {
    return client.get<{ data: EmailTemplate[]; total: number }>(
      "/api/v1/templates",
      {
        params: { campaign_id, skip, limit },
      },
    );
  },

  // Get template by ID
  get: async (id: number) => {
    return client.get<EmailTemplate>(`/api/v1/templates/${id}`);
  },

  // Create template
  create: async (data: EmailTemplateCreate) => {
    return client.post<EmailTemplate>("/api/v1/templates", data);
  },

  // Update template
  update: async (id: number, data: EmailTemplateUpdate) => {
    return client.patch<EmailTemplate>(`/api/v1/templates/${id}`, data);
  },

  // Delete template
  delete: async (id: number) => {
    return client.delete(`/api/v1/templates/${id}`);
  },

  // Preview template with sample variables
  preview: async (id: number, variables: Record<string, string>) => {
    return client.post<TemplatePreview>(`/api/v1/templates/${id}/preview`, {
      variables,
    });
  },
};

// Email Recipient endpoints
export const recipientAPI = {
  // Get recipients for campaign
  list: async (campaignId: number, skip: number = 0, limit: number = 20) => {
    return client.get<{ data: EmailRecipient[]; total: number }>(
      `/api/v1/campaigns/${campaignId}/recipients`,
      { params: { skip, limit } },
    );
  },

  // Add single recipient
  add: async (campaignId: number, data: EmailRecipientCreate) => {
    return client.post<EmailRecipient>(
      `/api/v1/campaigns/${campaignId}/recipients`,
      data,
    );
  },

  // Bulk add recipients (CSV format)
  bulkAdd: async (campaignId: number, recipients: EmailRecipientCreate[]) => {
    return client.post(`/api/v1/campaigns/${campaignId}/recipients/bulk`, {
      recipients,
    });
  },
};

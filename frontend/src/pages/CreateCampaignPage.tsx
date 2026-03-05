/**
 * Create Campaign Page
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { campaignAPI, templateAPI } from "../services/campaignAPI";
import type { EmailTemplate, CampaignCreate } from "../types/campaign";

export const CreateCampaignPage: React.FC = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    template_id: "",
    rate_limit: "100",
  });
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await templateAPI.list();
      setTemplates(response.data.data);
      if (response.data.data.length > 0) {
        setFormData((prev) => ({
          ...prev,
          template_id: response.data.data[0].id.toString(),
        }));
      }
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch templates",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.name.trim()) {
      setError("Campaign name is required");
      return;
    }

    if (!formData.template_id) {
      setError("Template is required");
      return;
    }

    try {
      const data: CampaignCreate = {
        name: formData.name,
        description: formData.description,
        template_id: parseInt(formData.template_id),
        rate_limit: parseInt(formData.rate_limit),
      };

      const response = await campaignAPI.create(data);
      setSuccess(true);

      // Redirect to campaign detail page
      setTimeout(() => {
        navigate(`/campaigns/${response.data.id}`);
      }, 1000);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to create campaign",
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate("/campaigns")}
            className="text-primary-600 hover:text-primary-700 text-sm font-semibold mb-4"
          >
            ← Back to Campaigns
          </button>
          <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
            Create Campaign
          </h1>
          <p className="text-slate-500 mt-0.5 text-sm">
            Set up a new email campaign
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-white border border-red-200 rounded-2xl shadow-sm">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="mb-6 p-4 bg-white border border-emerald-200 rounded-2xl shadow-sm">
            <p className="text-emerald-700">Campaign created successfully!</p>
          </div>
        )}

        {/* Form */}
        <form
          onSubmit={handleSubmit}
          className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-8"
        >
          {/* Campaign Name */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Campaign Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="e.g., Winter Newsletter 2024"
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
            />
          </div>

          {/* Description */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Description
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleChange}
              placeholder="Describe the purpose and target audience of this campaign"
              rows={4}
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
            ></textarea>
          </div>

          {/* Template Selection */}
          <div className="mb-6">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Email Template *
            </label>
            {templates.length === 0 ? (
              <div className="p-4 bg-amber-50 border border-amber-200 rounded-xl">
                <p className="text-amber-800 text-sm">
                  No templates available. Create a template first.
                </p>
                <button
                  type="button"
                  onClick={() => navigate("/templates/new")}
                  className="text-amber-600 hover:text-amber-800 font-semibold text-sm mt-2"
                >
                  Create Template →
                </button>
              </div>
            ) : (
              <select
                name="template_id"
                value={formData.template_id}
                onChange={handleChange}
                className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all bg-white"
              >
                {templates.map((template) => (
                  <option key={template.id} value={template.id}>
                    {template.name} (v{template.version})
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* Rate Limit */}
          <div className="mb-8">
            <label className="block text-sm font-semibold text-slate-900 mb-2">
              Rate Limit (emails/minute) *
            </label>
            <input
              type="number"
              name="rate_limit"
              value={formData.rate_limit}
              onChange={handleChange}
              min="1"
              max="1000"
              className="w-full px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
            />
            <p className="text-xs text-slate-500 mt-2">
              Controls how many emails are sent per minute to prevent server
              overload
            </p>
          </div>

          {/* Form Actions */}
          <div className="flex gap-4">
            <button
              type="submit"
              className="flex-1 bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-6 rounded-xl transition-all shadow-sm shadow-primary-600/20"
            >
              Create Campaign
            </button>
            <button
              type="button"
              onClick={() => navigate("/campaigns")}
              className="flex-1 bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-2.5 px-6 rounded-xl transition-all"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

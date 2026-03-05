/**
 * Template List Page
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { templateAPI } from "../services/campaignAPI";
import type { EmailTemplate } from "../types/campaign";

export const TemplateListPage: React.FC = () => {
  const navigate = useNavigate();
  const [templates, setTemplates] = useState<EmailTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await templateAPI.list();
      setTemplates(response.data.data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch templates",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this template?")) {
      return;
    }

    try {
      await templateAPI.delete(id);
      setTemplates(templates.filter((t) => t.id !== id));
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete template",
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Email Templates
            </h1>
            <p className="text-slate-500 mt-0.5 text-sm">
              Manage email templates
            </p>
          </div>
          <button
            onClick={() => navigate("/templates/new")}
            className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-5 rounded-xl transition-all shadow-sm shadow-primary-600/20"
          >
            + New Template
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-white border border-red-200 rounded-2xl shadow-sm">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Templates Grid */}
        {templates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200/60 shadow-sm">
            <div className="text-slate-400 text-4xl mb-4">📧</div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">
              No templates yet
            </h3>
            <p className="text-slate-500 mb-6">
              Create your first email template to get started
            </p>
            <button
              onClick={() => navigate("/templates/new")}
              className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-5 rounded-xl transition-all shadow-sm shadow-primary-600/20"
            >
              Create Template
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className="bg-white rounded-2xl border border-slate-200/60 overflow-hidden hover:shadow-md transition-all shadow-sm"
              >
                <div className="p-6">
                  <h3 className="text-lg font-bold text-slate-900 mb-2">
                    {template.name}
                  </h3>
                  <p className="text-slate-500 text-sm mb-4 line-clamp-2">
                    {template.subject}
                  </p>

                  {/* Template Preview */}
                  <div className="mb-4 p-3 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-700 line-clamp-3">
                    {template.body}
                  </div>

                  {/* Variables */}
                  {template.variables.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-slate-500 mb-2">
                        Variables:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {template.variables.map((variable) => (
                          <span
                            key={variable}
                            className="px-2 py-1 bg-primary-50 text-primary-700 rounded-lg text-xs font-medium"
                          >
                            {variable}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Version */}
                  <p className="text-xs text-slate-400 mb-4">
                    Version {template.version} • Created{" "}
                    {new Date(template.created_at).toLocaleDateString()}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/templates/${template.id}`)}
                      className="flex-1 text-primary-600 hover:text-primary-700 font-semibold text-sm py-2 px-3 border border-primary-200 rounded-xl hover:bg-primary-50 transition-all"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="flex-1 text-red-600 hover:text-red-700 font-semibold text-sm py-2 px-3 border border-red-200 rounded-xl hover:bg-red-50 transition-all"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

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
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">
              Email Templates
            </h1>
            <p className="text-gray-600 mt-2">Manage email templates</p>
          </div>
          <button
            onClick={() => navigate("/templates/new")}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
          >
            + New Template
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Templates Grid */}
        {templates.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <div className="text-gray-400 text-4xl mb-4">📧</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No templates yet
            </h3>
            <p className="text-gray-600 mb-6">
              Create your first email template to get started
            </p>
            <button
              onClick={() => navigate("/templates/new")}
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
            >
              Create Template
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.map((template) => (
              <div
                key={template.id}
                className="bg-white rounded-lg border border-gray-200 overflow-hidden hover:shadow-lg transition"
              >
                <div className="p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">
                    {template.name}
                  </h3>
                  <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                    {template.subject}
                  </p>

                  {/* Template Preview */}
                  <div className="mb-4 p-3 bg-gray-50 border border-gray-200 rounded text-sm text-gray-700 line-clamp-3">
                    {template.body}
                  </div>

                  {/* Variables */}
                  {template.variables.length > 0 && (
                    <div className="mb-4">
                      <p className="text-xs font-semibold text-gray-600 mb-2">
                        Variables:
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {template.variables.map((variable) => (
                          <span
                            key={variable}
                            className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-xs font-medium"
                          >
                            {variable}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Version */}
                  <p className="text-xs text-gray-500 mb-4">
                    Version {template.version} • Created{" "}
                    {new Date(template.created_at).toLocaleDateString()}
                  </p>

                  {/* Actions */}
                  <div className="flex gap-2">
                    <button
                      onClick={() => navigate(`/templates/${template.id}`)}
                      className="flex-1 text-blue-600 hover:text-blue-800 font-medium text-sm py-2 px-3 border border-blue-200 rounded-lg hover:bg-blue-50 transition"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDelete(template.id)}
                      className="flex-1 text-red-600 hover:text-red-800 font-medium text-sm py-2 px-3 border border-red-200 rounded-lg hover:bg-red-50 transition"
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

/**
 * Create/Edit Template Page
 */

import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { templateAPI } from "../services/campaignAPI";
import type {
  EmailTemplate,
  EmailTemplateCreate,
  EmailTemplateUpdate,
} from "../types/campaign";

export const CreateTemplatePage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const isEditing = !!id;

  const [formData, setFormData] = useState({
    name: "",
    subject: "",
    body: "",
  });
  const [template, setTemplate] = useState<EmailTemplate | null>(null);
  const [loading, setLoading] = useState(isEditing);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [preview, setPreview] = useState<{
    subject: string;
    body: string;
  } | null>(null);
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    if (isEditing && id) {
      fetchTemplate(parseInt(id));
    }
  }, [id, isEditing]);

  const fetchTemplate = async (templateId: number) => {
    try {
      const response = await templateAPI.get(templateId);
      setTemplate(response.data);
      setFormData({
        name: response.data.name,
        subject: response.data.subject,
        body: response.data.body,
      });
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to fetch template");
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handlePreview = async () => {
    if (!formData.subject || !formData.body) {
      setError("Subject and body are required for preview");
      return;
    }

    try {
      if (isEditing && id) {
        const response = await templateAPI.preview(parseInt(id), {
          name: "Sample",
          email: "user@example.com",
        });
        setPreview(response.data);
      } else {
        // For new templates, show a basic preview
        setPreview({
          subject: formData.subject.replace(/\{\{.*?\}\}/g, "Sample"),
          body: formData.body.replace(/\{\{.*?\}\}/g, "Sample"),
        });
      }
      setShowPreview(true);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to generate preview",
      );
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!formData.name.trim()) {
      setError("Template name is required");
      return;
    }

    if (!formData.subject.trim()) {
      setError("Subject is required");
      return;
    }

    if (!formData.body.trim()) {
      setError("Body is required");
      return;
    }

    try {
      if (isEditing && id) {
        const updateData: EmailTemplateUpdate = {
          name: formData.name,
          subject: formData.subject,
          body: formData.body,
        };
        await templateAPI.update(parseInt(id), updateData);
      } else {
        const createData: EmailTemplateCreate = {
          name: formData.name,
          subject: formData.subject,
          body: formData.body,
        };
        await templateAPI.create(createData);
      }
      setSuccess(true);
      setTimeout(() => {
        navigate("/templates");
      }, 1000);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : `Failed to ${isEditing ? "update" : "create"} template`,
      );
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => navigate("/templates")}
            className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-4"
          >
            ← Back to Templates
          </button>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditing ? "Edit Template" : "Create Template"}
          </h1>
          <p className="text-gray-600 mt-2">
            {isEditing
              ? "Update your email template"
              : "Create a new email template with variables"}
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Success Message */}
        {success && (
          <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
            <p className="text-green-800">
              Template {isEditing ? "updated" : "created"} successfully!
            </p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Form */}
          <div className="lg:col-span-2">
            <form
              onSubmit={handleSubmit}
              className="bg-white rounded-lg shadow-md p-8"
            >
              {/* Template Name */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Template Name *
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  placeholder="e.g., Welcome Email"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>

              {/* Subject */}
              <div className="mb-6">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Subject *
                </label>
                <input
                  type="text"
                  name="subject"
                  value={formData.subject}
                  onChange={handleChange}
                  placeholder="e.g., Welcome {{name}}!"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
                <p className="text-xs text-gray-600 mt-2">
                  Use {"{{variable}}"} for dynamic content
                </p>
              </div>

              {/* Body */}
              <div className="mb-8">
                <label className="block text-sm font-semibold text-gray-900 mb-2">
                  Email Body *
                </label>
                <textarea
                  name="body"
                  value={formData.body}
                  onChange={handleChange}
                  placeholder="Write your email content here. Use {{variable}} for dynamic content."
                  rows={12}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none font-mono text-sm"
                ></textarea>
                <p className="text-xs text-gray-600 mt-2">
                  Supports HTML and Jinja2 template syntax
                </p>
              </div>

              {/* Actions */}
              <div className="flex gap-4">
                <button
                  type="button"
                  onClick={handlePreview}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-6 rounded-lg transition"
                >
                  Preview
                </button>
                <button
                  type="submit"
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
                >
                  {isEditing ? "Update Template" : "Create Template"}
                </button>
                <button
                  type="button"
                  onClick={() => navigate("/templates")}
                  className="flex-1 bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-6 rounded-lg transition"
                >
                  Cancel
                </button>
              </div>
            </form>
          </div>

          {/* Info Sidebar */}
          <div>
            <div className="bg-white rounded-lg shadow-md p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Template Info
              </h3>

              {isEditing && template && (
                <>
                  <div className="mb-4">
                    <p className="text-xs text-gray-600 font-medium">Version</p>
                    <p className="text-lg text-gray-900 font-semibold">
                      {template.version}
                    </p>
                  </div>
                  <div className="mb-4">
                    <p className="text-xs text-gray-600 font-medium">Created</p>
                    <p className="text-sm text-gray-900">
                      {new Date(template.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </>
              )}

              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-semibold text-gray-900 mb-3">
                  Variable Help
                </h4>
                <p className="text-xs text-gray-600 mb-3">
                  Use double curly braces to insert variables:
                </p>
                <div className="space-y-2 text-xs">
                  <div className="p-2 bg-gray-50 rounded font-mono text-gray-700">
                    {"{{"} name {"}}"}
                  </div>
                  <div className="p-2 bg-gray-50 rounded font-mono text-gray-700">
                    {"{{"} email {"}}"}
                  </div>
                  <div className="p-2 bg-gray-50 rounded font-mono text-gray-700">
                    {"{{"} custom_var {"}}"}
                  </div>
                </div>
              </div>

              {showPreview && preview && (
                <div className="mt-6 border-t border-gray-200 pt-4">
                  <h4 className="text-sm font-semibold text-gray-900 mb-3">
                    Preview
                  </h4>
                  <div className="space-y-2 text-xs">
                    <div>
                      <p className="text-gray-600 font-medium mb-1">Subject:</p>
                      <p className="p-2 bg-gray-50 rounded text-gray-900">
                        {preview.subject}
                      </p>
                    </div>
                    <div>
                      <p className="text-gray-600 font-medium mb-1">Body:</p>
                      <div className="p-2 bg-gray-50 rounded text-gray-900 max-h-64 overflow-y-auto whitespace-pre-wrap">
                        {preview.body}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

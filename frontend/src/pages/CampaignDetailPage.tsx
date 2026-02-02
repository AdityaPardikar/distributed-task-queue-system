/**
 * Campaign Detail Page
 */

import React, { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { campaignAPI, recipientAPI } from "../services/campaignAPI";
import type {
  Campaign,
  CampaignStatus,
  EmailRecipient,
} from "../types/campaign";

export const CampaignDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<Campaign | null>(null);
  const [status, setStatus] = useState<CampaignStatus | null>(null);
  const [recipients, setRecipients] = useState<EmailRecipient[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"overview" | "recipients">(
    "overview",
  );
  const [showAddRecipient, setShowAddRecipient] = useState(false);
  const [newRecipientEmail, setNewRecipientEmail] = useState("");

  const campaignId = id ? parseInt(id) : null;

  const fetchData = useCallback(async () => {
    if (!campaignId) return;
    try {
      setLoading(true);
      const [campaignRes, statusRes, recipientsRes] = await Promise.all([
        campaignAPI.get(campaignId),
        campaignAPI.getStatus(campaignId),
        recipientAPI.list(campaignId),
      ]);
      setCampaign(campaignRes.data);
      setStatus(statusRes.data);
      setRecipients(recipientsRes.data.data);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch campaign data",
      );
    } finally {
      setLoading(false);
    }
  }, [campaignId]);

  useEffect(() => {
    if (campaignId) {
      fetchData();
    }
  }, [campaignId, fetchData]);

  const handleAddRecipient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!campaignId || !newRecipientEmail.trim()) return;

    try {
      await recipientAPI.add(campaignId, {
        email: newRecipientEmail,
        variables: {},
      });
      setNewRecipientEmail("");
      setShowAddRecipient(false);
      fetchData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to add recipient");
    }
  };

  const handleLaunch = async () => {
    if (!campaignId) return;
    try {
      await campaignAPI.launch(campaignId);
      fetchData();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to launch campaign",
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

  if (!campaign) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-gray-600 text-lg">Campaign not found</p>
          <button
            onClick={() => navigate("/campaigns")}
            className="text-blue-600 hover:text-blue-800 font-medium mt-4"
          >
            Back to Campaigns
          </button>
        </div>
      </div>
    );
  }

  const progress = status
    ? Math.round(
        ((status.completed_tasks + status.failed_tasks) / status.total_tasks) *
          100,
      ) || 0
    : 0;

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => navigate("/campaigns")}
              className="text-blue-600 hover:text-blue-800 text-sm font-medium mb-4"
            >
              ← Back to Campaigns
            </button>
            <h1 className="text-3xl font-bold text-gray-900">
              {campaign.name}
            </h1>
            <p className="text-gray-600 mt-2">{campaign.description}</p>
          </div>
          <div className="flex gap-2">
            {campaign.status === "draft" && (
              <button
                onClick={handleLaunch}
                className="bg-green-600 hover:bg-green-700 text-white font-semibold py-2 px-6 rounded-lg transition"
              >
                Launch Campaign
              </button>
            )}
            <button
              onClick={() => navigate("/campaigns")}
              className="bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-6 rounded-lg transition"
            >
              Close
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <p className="text-gray-600 text-sm font-medium">Status</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {campaign.status}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <p className="text-gray-600 text-sm font-medium">Total Tasks</p>
            <p className="text-2xl font-bold text-gray-900 mt-2">
              {status?.total_tasks || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <p className="text-gray-600 text-sm font-medium">Completed</p>
            <p className="text-2xl font-bold text-green-600 mt-2">
              {status?.completed_tasks || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg p-4 border border-gray-200">
            <p className="text-gray-600 text-sm font-medium">Failed</p>
            <p className="text-2xl font-bold text-red-600 mt-2">
              {status?.failed_tasks || 0}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-lg p-6 border border-gray-200 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Progress</h2>
          <div className="w-full bg-gray-200 rounded-full h-4">
            <div
              className="bg-blue-600 h-4 rounded-full transition"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-gray-600 mt-3">
            {progress}% complete ({status?.completed_tasks || 0}/
            {status?.total_tasks || 0} emails sent)
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 font-medium transition ${
              activeTab === "overview"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("recipients")}
            className={`px-4 py-2 font-medium transition ${
              activeTab === "recipients"
                ? "text-blue-600 border-b-2 border-blue-600"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            Recipients ({recipients.length})
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Campaign Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-gray-600 font-medium">Created</p>
                <p className="text-gray-900 mt-1">
                  {new Date(campaign.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">
                  Last Updated
                </p>
                <p className="text-gray-900 mt-1">
                  {new Date(campaign.updated_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Rate Limit</p>
                <p className="text-gray-900 mt-1">
                  {campaign.rate_limit} emails/minute
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 font-medium">Template</p>
                <p className="text-gray-900 mt-1">
                  Template ID: {campaign.template_id}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recipients Tab */}
        {activeTab === "recipients" && (
          <div className="bg-white rounded-lg border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-semibold text-gray-900">
                Recipients
              </h2>
              <button
                onClick={() => setShowAddRecipient(!showAddRecipient)}
                className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-4 rounded-lg transition text-sm"
              >
                + Add Recipient
              </button>
            </div>

            {/* Add Recipient Form */}
            {showAddRecipient && (
              <form
                onSubmit={handleAddRecipient}
                className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg"
              >
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={newRecipientEmail}
                    onChange={(e) => setNewRecipientEmail(e.target.value)}
                    placeholder="Enter email address"
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                  />
                  <button
                    type="submit"
                    className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddRecipient(false)}
                    className="bg-gray-200 hover:bg-gray-300 text-gray-900 font-semibold py-2 px-6 rounded-lg transition"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            {/* Recipients List */}
            {recipients.length === 0 ? (
              <div className="text-center py-8 text-gray-600">
                <p>No recipients added yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-2 text-left font-semibold text-gray-900">
                        Email
                      </th>
                      <th className="px-4 py-2 text-left font-semibold text-gray-900">
                        Status
                      </th>
                      <th className="px-4 py-2 text-left font-semibold text-gray-900">
                        Added
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recipients.map((recipient) => (
                      <tr
                        key={recipient.id}
                        className="border-b border-gray-200 hover:bg-gray-50"
                      >
                        <td className="px-4 py-2">{recipient.email}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              recipient.status === "sent"
                                ? "bg-green-100 text-green-800"
                                : recipient.status === "failed"
                                  ? "bg-red-100 text-red-800"
                                  : "bg-yellow-100 text-yellow-800"
                            }`}
                          >
                            {recipient.status}
                          </span>
                        </td>
                        <td className="px-4 py-2">
                          {new Date(recipient.created_at).toLocaleDateString()}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

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
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!campaign) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-slate-500 text-lg">Campaign not found</p>
          <button
            onClick={() => navigate("/campaigns")}
            className="text-primary-600 hover:text-primary-700 font-semibold mt-4"
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
    <div className="space-y-6 animate-fade-in">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-start mb-8">
          <div>
            <button
              onClick={() => navigate("/campaigns")}
              className="text-primary-600 hover:text-primary-700 text-sm font-semibold mb-4"
            >
              ← Back to Campaigns
            </button>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              {campaign.name}
            </h1>
            <p className="text-slate-500 mt-0.5 text-sm">
              {campaign.description}
            </p>
          </div>
          <div className="flex gap-2">
            {campaign.status === "draft" && (
              <button
                onClick={handleLaunch}
                className="bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 px-5 rounded-xl transition-all"
              >
                Launch Campaign
              </button>
            )}
            <button
              onClick={() => navigate("/campaigns")}
              className="bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-2.5 px-5 rounded-xl transition-all"
            >
              Close
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-white border border-red-200 rounded-2xl shadow-sm">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Status Cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm">
            <p className="text-slate-500 text-sm font-medium">Status</p>
            <p className="text-2xl font-bold text-slate-900 mt-2">
              {campaign.status}
            </p>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm">
            <p className="text-slate-500 text-sm font-medium">Total Tasks</p>
            <p className="text-2xl font-bold text-slate-900 mt-2">
              {status?.total_tasks || 0}
            </p>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm">
            <p className="text-slate-500 text-sm font-medium">Completed</p>
            <p className="text-2xl font-bold text-emerald-600 mt-2">
              {status?.completed_tasks || 0}
            </p>
          </div>
          <div className="bg-white rounded-2xl p-5 border border-slate-200/60 shadow-sm">
            <p className="text-slate-500 text-sm font-medium">Failed</p>
            <p className="text-2xl font-bold text-red-600 mt-2">
              {status?.failed_tasks || 0}
            </p>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="bg-white rounded-2xl p-6 border border-slate-200/60 shadow-sm mb-8">
          <h2 className="text-lg font-bold text-slate-900 mb-4">Progress</h2>
          <div className="w-full bg-slate-100 rounded-full h-3">
            <div
              className="bg-gradient-to-r from-primary-500 to-violet-500 h-3 rounded-full transition-all duration-500"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p className="text-sm text-slate-500 mt-3">
            {progress}% complete ({status?.completed_tasks || 0}/
            {status?.total_tasks || 0} emails sent)
          </p>
        </div>

        {/* Tabs */}
        <div className="flex gap-4 mb-6 border-b border-slate-200">
          <button
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 font-semibold transition ${
              activeTab === "overview"
                ? "text-primary-600 border-b-2 border-primary-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Overview
          </button>
          <button
            onClick={() => setActiveTab("recipients")}
            className={`px-4 py-2 font-semibold transition ${
              activeTab === "recipients"
                ? "text-primary-600 border-b-2 border-primary-600"
                : "text-slate-500 hover:text-slate-900"
            }`}
          >
            Recipients ({recipients.length})
          </button>
        </div>

        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <h2 className="text-lg font-bold text-slate-900 mb-4">
              Campaign Details
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <p className="text-sm text-slate-500 font-medium">Created</p>
                <p className="text-slate-900 mt-1">
                  {new Date(campaign.created_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">
                  Last Updated
                </p>
                <p className="text-slate-900 mt-1">
                  {new Date(campaign.updated_at).toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">Rate Limit</p>
                <p className="text-slate-900 mt-1">
                  {campaign.rate_limit} emails/minute
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500 font-medium">Template</p>
                <p className="text-slate-900 mt-1">
                  Template ID: {campaign.template_id}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Recipients Tab */}
        {activeTab === "recipients" && (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm p-6">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-lg font-bold text-slate-900">Recipients</h2>
              <button
                onClick={() => setShowAddRecipient(!showAddRecipient)}
                className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2 px-4 rounded-xl transition-all text-sm shadow-sm shadow-primary-600/20"
              >
                + Add Recipient
              </button>
            </div>

            {/* Add Recipient Form */}
            {showAddRecipient && (
              <form
                onSubmit={handleAddRecipient}
                className="mb-6 p-4 bg-slate-50 border border-slate-200 rounded-xl"
              >
                <div className="flex gap-2">
                  <input
                    type="email"
                    value={newRecipientEmail}
                    onChange={(e) => setNewRecipientEmail(e.target.value)}
                    placeholder="Enter email address"
                    className="flex-1 px-4 py-2.5 border border-slate-200 rounded-xl focus:ring-4 focus:ring-primary-500/10 focus:border-primary-500 outline-none transition-all"
                  />
                  <button
                    type="submit"
                    className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-6 rounded-xl transition-all"
                  >
                    Add
                  </button>
                  <button
                    type="button"
                    onClick={() => setShowAddRecipient(false)}
                    className="bg-slate-100 hover:bg-slate-200 text-slate-900 font-semibold py-2.5 px-6 rounded-xl transition-all"
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}

            {/* Recipients List */}
            {recipients.length === 0 ? (
              <div className="text-center py-8 text-slate-500">
                <p>No recipients added yet</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="border-b border-slate-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Email
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Status
                      </th>
                      <th className="px-4 py-3 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                        Added
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {recipients.map((recipient) => (
                      <tr
                        key={recipient.id}
                        className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
                      >
                        <td className="px-4 py-2">{recipient.email}</td>
                        <td className="px-4 py-2">
                          <span
                            className={`px-2 py-1 rounded text-xs font-semibold ${
                              recipient.status === "sent"
                                ? "bg-emerald-50 text-emerald-700"
                                : recipient.status === "failed"
                                  ? "bg-red-50 text-red-700"
                                  : "bg-amber-50 text-amber-700"
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

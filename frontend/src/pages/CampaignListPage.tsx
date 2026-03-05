/**
 * Campaign List Page
 */

import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { campaignAPI } from "../services/campaignAPI";
import type { Campaign, CampaignStatus } from "../types/campaign";

export const CampaignListPage: React.FC = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statuses, setStatuses] = useState<Record<number, CampaignStatus>>({});

  useEffect(() => {
    fetchCampaigns();
  }, []);

  const fetchCampaigns = async () => {
    try {
      setLoading(true);
      const response = await campaignAPI.list(0, 50);
      setCampaigns(response.data.data);

      // Fetch status for each campaign
      const newStatuses: Record<number, CampaignStatus> = {};
      for (const campaign of response.data.data) {
        try {
          const status = await campaignAPI.getStatus(campaign.id);
          newStatuses[campaign.id] = status.data;
        } catch {
          console.error(`Failed to fetch status for campaign ${campaign.id}`);
        }
      }
      setStatuses(newStatuses);
      setError(null);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch campaigns",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!window.confirm("Are you sure you want to delete this campaign?")) {
      return;
    }

    try {
      await campaignAPI.delete(id);
      setCampaigns(campaigns.filter((c) => c.id !== id));
      const newStatuses = { ...statuses };
      delete newStatuses[id];
      setStatuses(newStatuses);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to delete campaign",
      );
    }
  };

  const handleLaunch = async (id: number) => {
    try {
      await campaignAPI.launch(id);
      fetchCampaigns();
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to launch campaign",
      );
    }
  };

  const handlePause = async (id: number) => {
    try {
      await campaignAPI.pause(id);
      fetchCampaigns();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to pause campaign");
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft":
        return "bg-slate-100 text-slate-700";
      case "scheduled":
        return "bg-primary-50 text-primary-700";
      case "running":
        return "bg-emerald-50 text-emerald-700";
      case "paused":
        return "bg-amber-50 text-amber-700";
      case "completed":
        return "bg-violet-50 text-violet-700";
      case "failed":
        return "bg-red-50 text-red-700";
      default:
        return "bg-slate-100 text-slate-700";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-slate-500">Loading campaigns...</p>
        </div>
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
              Campaigns
            </h1>
            <p className="text-slate-500 mt-0.5 text-sm">
              Manage email campaigns
            </p>
          </div>
          <button
            onClick={() => navigate("/campaigns/new")}
            className="bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-5 rounded-xl transition-all shadow-sm shadow-primary-600/20"
          >
            + New Campaign
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-white border border-red-200 rounded-2xl shadow-sm">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Campaigns Table */}
        {campaigns.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-2xl border border-slate-200/60 shadow-sm">
            <div className="text-slate-400 mb-2">📧</div>
            <h3 className="text-lg font-bold text-slate-900 mb-2">
              No campaigns yet
            </h3>
            <p className="text-slate-500 mb-6">
              Create your first email campaign to get started
            </p>
            <button
              onClick={() => navigate("/campaigns/new")}
              className="inline-block bg-primary-600 hover:bg-primary-700 text-white font-semibold py-2.5 px-5 rounded-xl transition-all shadow-sm shadow-primary-600/20"
            >
              Create Campaign
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-2xl border border-slate-200/60 shadow-sm overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-100">
                  <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Name
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Progress
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Created
                  </th>
                  <th className="px-6 py-3.5 text-left text-xs font-bold text-slate-400 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {campaigns.map((campaign) => {
                  const status = statuses[campaign.id] || {
                    total_tasks: 0,
                    completed_tasks: 0,
                    failed_tasks: 0,
                    pending_tasks: 0,
                  };
                  const progress =
                    status.total_tasks > 0
                      ? Math.round(
                          ((status.completed_tasks + status.failed_tasks) /
                            status.total_tasks) *
                            100,
                        )
                      : 0;

                  return (
                    <tr
                      key={campaign.id}
                      className="border-b border-slate-100 hover:bg-slate-50/50 transition-colors"
                    >
                      <td className="px-6 py-4">
                        <button
                          onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          className="text-primary-600 hover:text-primary-700 font-semibold"
                        >
                          {campaign.name}
                        </button>
                        <p className="text-sm text-slate-400 mt-1">
                          {campaign.description}
                        </p>
                      </td>
                      <td className="px-6 py-4">
                        <span
                          className={`inline-block px-3 py-1 rounded-full text-sm font-semibold ${getStatusColor(
                            campaign.status,
                          )}`}
                        >
                          {campaign.status}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="w-full bg-slate-100 rounded-full h-2">
                          <div
                            className="bg-primary-600 h-2 rounded-full transition"
                            style={{ width: `${progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-slate-500 mt-2">
                          {status.completed_tasks}/{status.total_tasks} sent
                        </p>
                      </td>
                      <td className="px-6 py-4 text-sm text-slate-500">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          {campaign.status === "draft" && (
                            <button
                              onClick={() => handleLaunch(campaign.id)}
                              className="text-emerald-600 hover:text-emerald-700 text-sm font-semibold"
                            >
                              Launch
                            </button>
                          )}
                          {campaign.status === "running" && (
                            <button
                              onClick={() => handlePause(campaign.id)}
                              className="text-amber-600 hover:text-amber-700 text-sm font-semibold"
                            >
                              Pause
                            </button>
                          )}
                          <button
                            onClick={() =>
                              navigate(`/campaigns/${campaign.id}`)
                            }
                            className="text-primary-600 hover:text-primary-700 text-sm font-semibold"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDelete(campaign.id)}
                            className="text-red-600 hover:text-red-700 text-sm font-semibold"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

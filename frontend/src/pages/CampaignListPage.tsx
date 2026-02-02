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
        } catch (err) {
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
        return "bg-gray-100 text-gray-800";
      case "scheduled":
        return "bg-blue-100 text-blue-800";
      case "running":
        return "bg-green-100 text-green-800";
      case "paused":
        return "bg-yellow-100 text-yellow-800";
      case "completed":
        return "bg-purple-100 text-purple-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Campaigns</h1>
            <p className="text-gray-600 mt-2">Manage email campaigns</p>
          </div>
          <button
            onClick={() => navigate("/campaigns/new")}
            className="bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
          >
            + New Campaign
          </button>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-800">{error}</p>
          </div>
        )}

        {/* Campaigns Table */}
        {campaigns.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg border border-gray-200">
            <div className="text-gray-400 mb-2">📧</div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              No campaigns yet
            </h3>
            <p className="text-gray-600 mb-6">
              Create your first email campaign to get started
            </p>
            <button
              onClick={() => navigate("/campaigns/new")}
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 px-6 rounded-lg transition"
            >
              Create Campaign
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-50 border-b border-gray-200">
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">
                    Name
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">
                    Progress
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">
                    Created
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-semibold text-gray-900">
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
                      className="border-b border-gray-200 hover:bg-gray-50"
                    >
                      <td className="px-6 py-4">
                        <button
                          onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          className="text-blue-600 hover:text-blue-800 font-medium"
                        >
                          {campaign.name}
                        </button>
                        <p className="text-sm text-gray-500 mt-1">
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
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-600 h-2 rounded-full transition"
                            style={{ width: `${progress}%` }}
                          ></div>
                        </div>
                        <p className="text-xs text-gray-600 mt-2">
                          {status.completed_tasks}/{status.total_tasks} sent
                        </p>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-600">
                        {new Date(campaign.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          {campaign.status === "draft" && (
                            <button
                              onClick={() => handleLaunch(campaign.id)}
                              className="text-green-600 hover:text-green-800 text-sm font-medium"
                            >
                              Launch
                            </button>
                          )}
                          {campaign.status === "running" && (
                            <button
                              onClick={() => handlePause(campaign.id)}
                              className="text-yellow-600 hover:text-yellow-800 text-sm font-medium"
                            >
                              Pause
                            </button>
                          )}
                          <button
                            onClick={() =>
                              navigate(`/campaigns/${campaign.id}`)
                            }
                            className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleDelete(campaign.id)}
                            className="text-red-600 hover:text-red-800 text-sm font-medium"
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

/**
 * EmptyState – zero-data illustration + CTA shown when a list has no items.
 */
import React from "react";
import { InboxIcon } from "lucide-react";

interface EmptyStateProps {
  /** Main heading */
  title?: string;
  /** Supporting sentence */
  description?: string;
  /** Optional lucide icon (defaults to InboxIcon) */
  icon?: React.ReactNode;
  /** Optional call-to-action */
  action?: {
    label: string;
    onClick: () => void;
  };
  className?: string;
}

const EmptyState: React.FC<EmptyStateProps> = ({
  title = "Nothing here yet",
  description = "Get started by creating your first item.",
  icon,
  action,
  className = "",
}) => (
  <div
    className={`flex flex-col items-center justify-center py-16 text-center ${className}`}
  >
    <div className="w-16 h-16 bg-slate-100 rounded-2xl flex items-center justify-center mb-4">
      {icon ?? <InboxIcon className="w-8 h-8 text-slate-400" />}
    </div>
    <h3 className="text-lg font-bold text-slate-900 mb-1">{title}</h3>
    <p className="text-sm text-slate-500 max-w-xs">{description}</p>
    {action && (
      <button
        onClick={action.onClick}
        className="mt-6 px-5 py-2.5 bg-primary-600 text-white text-sm font-semibold rounded-xl
                   hover:bg-primary-700 transition-all focus:outline-none focus:ring-4
                   focus:ring-primary-500/20 shadow-sm shadow-primary-600/20"
      >
        {action.label}
      </button>
    )}
  </div>
);

export default EmptyState;

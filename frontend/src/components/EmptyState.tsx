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
    <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mb-4">
      {icon ?? <InboxIcon className="w-8 h-8 text-gray-400" />}
    </div>
    <h3 className="text-lg font-semibold text-gray-900 mb-1">{title}</h3>
    <p className="text-sm text-gray-500 max-w-xs">{description}</p>
    {action && (
      <button
        onClick={action.onClick}
        className="mt-6 px-5 py-2.5 bg-primary-600 text-white text-sm font-medium rounded-lg
                   hover:bg-primary-700 transition-colors focus:outline-none focus:ring-2
                   focus:ring-primary-500 focus:ring-offset-2"
      >
        {action.label}
      </button>
    )}
  </div>
);

export default EmptyState;

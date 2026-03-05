import React from "react";

interface LoadingFallbackProps {
  message?: string;
  fullPage?: boolean;
}

/**
 * Loading fallback component for lazy-loaded pages.
 * Uses CSS classes defined in index.css (loading-fallback, loading-spinner, spinner-ring).
 */
const LoadingFallback: React.FC<LoadingFallbackProps> = ({
  message = "Loading...",
  fullPage = true,
}) => {
  return (
    <div className={`loading-fallback ${fullPage ? "full-page" : ""}`}>
      <div className="loading-content">
        <div className="loading-spinner">
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
          <div className="spinner-ring"></div>
        </div>
        <p className="loading-message">{message}</p>
      </div>
    </div>
  );
};

export default LoadingFallback;

import React from "react";
import "../styles/loading-fallback.css";

interface LoadingFallbackProps {
  message?: string;
  fullPage?: boolean;
}

/**
 * Loading fallback component for lazy-loaded pages
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

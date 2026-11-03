import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export function ErrorAlert({
  title = 'Failed to load data',
  message,
  onRetry,
  className = '',
}) {
  const displayMsg =
    typeof message === 'string'
      ? message
      : message?.message || 'A network or server error occurred while retrieving data.';

  return (
    <div className={`error-alert ${className}`}>
      <div className="error-alert-icon">
        <AlertTriangle size={22} />
      </div>
      <div className="error-alert-content">
        <h4 className="error-alert-title">{title}</h4>
        <p className="error-alert-text">{displayMsg}</p>
      </div>
      {onRetry && (
        <button type="button" className="error-retry-btn" onClick={onRetry}>
          <RefreshCw size={14} className="retry-icon" />
          <span>Retry</span>
        </button>
      )}
    </div>
  );
}

export default ErrorAlert;

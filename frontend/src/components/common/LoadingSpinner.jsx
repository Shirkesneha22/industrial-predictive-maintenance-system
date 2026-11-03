import React from 'react';
import { Loader2 } from 'lucide-react';

export function LoadingSpinner({
  size = 28,
  message = 'Loading telemetry & risk metrics...',
  inline = false,
  className = '',
}) {
  if (inline) {
    return (
      <span className={`inline-spinner ${className}`}>
        <Loader2 size={size} className="spin-animation" />
        {message && <span className="spinner-msg-inline">{message}</span>}
      </span>
    );
  }

  return (
    <div className={`loading-container ${className}`}>
      <Loader2 size={size} className="spin-animation spinner-primary" />
      {message && <p className="loading-text">{message}</p>}
    </div>
  );
}

export function SkeletonLoader({ rows = 3, className = '' }) {
  return (
    <div className={`skeleton-wrapper ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="skeleton-row"
          style={{ width: `${100 - (i % 3) * 15}%` }}
        />
      ))}
    </div>
  );
}

export default LoadingSpinner;

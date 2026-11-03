import React from 'react';

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  variant = 'default',
  trend,
  className = '',
}) {
  const variantStyles = {
    default: 'stat-default',
    normal: 'stat-normal',
    warning: 'stat-warning',
    critical: 'stat-critical',
    info: 'stat-info',
  };

  const styleClass = variantStyles[variant] || variantStyles.default;

  return (
    <div className={`stat-card ${styleClass} ${className}`}>
      <div className="stat-card-header">
        <span className="stat-card-title">{title}</span>
        {Icon && (
          <div className="stat-card-icon">
            <Icon size={20} />
          </div>
        )}
      </div>
      <div className="stat-card-body">
        <div className="stat-card-value">{value}</div>
        {(subtitle || trend) && (
          <div className="stat-card-footer">
            {trend && <span className="stat-card-trend">{trend}</span>}
            {subtitle && <span className="stat-card-subtitle">{subtitle}</span>}
          </div>
        )}
      </div>
    </div>
  );
}

export default StatCard;

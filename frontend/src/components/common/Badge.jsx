import React from 'react';

/**
 * Standard badge component for risk severity, status, and sensors.
 */
export function Badge({ children, variant = 'default', size = 'md', className = '' }) {
  const variantClasses = {
    normal: 'badge-normal',
    warning: 'badge-warning',
    critical: 'badge-critical',
    info: 'badge-info',
    success: 'badge-success',
    neutral: 'badge-neutral',
    default: 'badge-neutral',
  };

  const normalizedVariant = children
    ? String(children).toLowerCase()
    : variant;

  let resolvedClass = variantClasses[variant] || variantClasses.default;
  if (normalizedVariant.includes('normal')) {
    resolvedClass = variantClasses.normal;
  } else if (normalizedVariant.includes('warning')) {
    resolvedClass = variantClasses.warning;
  } else if (normalizedVariant.includes('critical')) {
    resolvedClass = variantClasses.critical;
  } else if (normalizedVariant.includes('fault') || normalizedVariant.includes('invalid')) {
    resolvedClass = variantClasses.critical;
  }

  const sizeClass = size === 'sm' ? 'badge-sm' : size === 'lg' ? 'badge-lg' : 'badge-md';

  return (
    <span className={`badge ${resolvedClass} ${sizeClass} ${className}`}>
      {children}
    </span>
  );
}

export default Badge;

import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  Activity,
  Cpu,
  BarChart3,
  Database,
  ShieldAlert,
  Wrench,
  X,
} from 'lucide-react';

const navItems = [
  {
    name: 'Overview',
    path: '/',
    icon: Activity,
    description: 'Fleet health & condition',
  },
  {
    name: 'Machines',
    path: '/machines',
    icon: Cpu,
    description: 'Machine list & telemetry',
  },
  {
    name: 'Maintenance',
    path: '/maintenance',
    icon: Wrench,
    description: 'Work orders & failure logs',
  },
  {
    name: 'Evaluation',
    path: '/evaluation',
    icon: BarChart3,
    description: 'Model metrics & benchmark',
  },
  {
    name: 'Data Quality',
    path: '/data-quality',
    icon: Database,
    description: 'Sensor health & telemetry QA',
  },
];

export function Sidebar({ isOpen, onClose }) {
  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && <div className="sidebar-backdrop" onClick={onClose} />}

      <aside className={`sidebar-container ${isOpen ? 'sidebar-open' : ''}`}>
        <div className="sidebar-header">
          <div className="sidebar-brand">
            <div className="brand-icon">
              <Wrench size={22} />
            </div>
            <div className="brand-text">
              <span className="brand-title">PredixAI</span>
              <span className="brand-subtitle">Predictive Maintenance</span>
            </div>
          </div>
          <button
            type="button"
            className="sidebar-close-btn"
            onClick={onClose}
            aria-label="Close navigation"
          >
            <X size={20} />
          </button>
        </div>

        <div className="sidebar-divider" />

        <div className="sidebar-nav-section">
          <div className="sidebar-section-label">MONITORING CONSOLE</div>
          <nav className="sidebar-nav">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <NavLink
                  key={item.path}
                  to={item.path}
                  end={item.path === '/'}
                  className={({ isActive }) =>
                    `sidebar-link ${isActive ? 'sidebar-link-active' : ''}`
                  }
                  onClick={() => {
                    if (window.innerWidth < 1024) onClose();
                  }}
                >
                  <Icon size={19} className="sidebar-link-icon" />
                  <div className="sidebar-link-content">
                    <span className="sidebar-link-name">{item.name}</span>
                    <span className="sidebar-link-desc">{item.description}</span>
                  </div>
                </NavLink>
              );
            })}
          </nav>
        </div>

        <div className="sidebar-footer">
          <div className="sidebar-status-card">
            <div className="sidebar-status-indicator">
              <span className="status-dot-pulse" />
              <span className="status-label">Engine Active</span>
            </div>
            <p className="sidebar-status-sub">Anti-Leakage Protected</p>
          </div>
        </div>
      </aside>
    </>
  );
}

export default Sidebar;

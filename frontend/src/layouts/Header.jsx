import React, { useState, useEffect } from 'react';
import { Menu, Activity, Clock, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import apiClient from '../services/api';

export function Header({ onToggleSidebar, pageTitle }) {
  const [currentTime, setCurrentTime] = useState(new Date().toUTCString());
  const [serverStatus, setServerStatus] = useState('checking'); // 'healthy' | 'unreachable' | 'checking'

  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date().toUTCString());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    let isMounted = true;
    async function checkHealth() {
      try {
        await apiClient.get('/health', { baseURL: 'http://localhost:8000' });
        if (isMounted) setServerStatus('healthy');
      } catch (e) {
        // Fallback test against default baseURL
        try {
          await apiClient.get('/machines', { params: { page_size: 1 } });
          if (isMounted) setServerStatus('healthy');
        } catch {
          if (isMounted) setServerStatus('unreachable');
        }
      }
    }
    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  return (
    <header className="dashboard-header">
      <div className="header-left">
        <button
          type="button"
          className="header-menu-btn"
          onClick={onToggleSidebar}
          aria-label="Toggle navigation menu"
        >
          <Menu size={22} />
        </button>
        <div className="header-titles">
          <h1 className="header-title">{pageTitle || 'Predictive Maintenance'}</h1>
        </div>
      </div>

      <div className="header-right">
        {/* UTC Clock */}
        <div className="header-meta-item header-time">
          <Clock size={15} />
          <span>{currentTime}</span>
        </div>

        {/* Server Connection Badge */}
        <div className="header-meta-item">
          {serverStatus === 'healthy' ? (
            <span className="api-status-badge api-status-online" title="Connected to FastAPI backend">
              <CheckCircle2 size={14} />
              <span>Backend Online</span>
            </span>
          ) : serverStatus === 'unreachable' ? (
            <span className="api-status-badge api-status-offline" title="Backend not reachable at localhost:8000">
              <AlertCircle size={14} />
              <span>Backend Offline</span>
            </span>
          ) : (
            <span className="api-status-badge api-status-checking">
              <Activity size={14} className="spin-animation" />
              <span>Connecting...</span>
            </span>
          )}
        </div>

        {/* Anti-leakage badge */}
        <div className="header-meta-item anti-leakage-pill" title="Predictions respect strict cutoff boundaries">
          <ShieldCheck size={14} />
          <span>Zero Data Leakage</span>
        </div>
      </div>
    </header>
  );
}

export default Header;

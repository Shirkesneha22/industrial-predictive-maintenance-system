import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from './Sidebar';
import Header from './Header';

const pageTitleMap = {
  '/': 'Fleet Overview',
  '/machines': 'Monitored Equipment Fleet',
  '/evaluation': 'Model Performance & Benchmark',
  '/data-quality': 'Telemetry & Sensor Data Quality',
};

export function DashboardLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Find matching title or default
  let currentTitle = pageTitleMap[location.pathname];
  if (!currentTitle) {
    if (location.pathname.startsWith('/machines/')) {
      currentTitle = 'Machine Diagnostic Telemetry';
    } else {
      currentTitle = 'Predictive Maintenance Console';
    }
  }

  return (
    <div className="app-layout">
      <Sidebar
        isOpen={sidebarOpen}
        onClose={() => setSidebarOpen(false)}
      />

      <div className="main-wrapper">
        <Header
          pageTitle={currentTitle}
          onToggleSidebar={() => setSidebarOpen((prev) => !prev)}
        />
        <main className="content-container">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;

import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DashboardLayout } from './layouts';
import {
  OverviewPage,
  MachinesPage,
  MachineDetailPage,
  MaintenancePage,
  EvaluationPage,
  DataQualityPage,
  NotFoundPage,
} from './pages';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardLayout />}>
          <Route index element={<OverviewPage />} />
          <Route path="machines" element={<MachinesPage />} />
          <Route path="machines/:id" element={<MachineDetailPage />} />
          <Route path="maintenance" element={<MaintenancePage />} />
          <Route path="evaluation" element={<EvaluationPage />} />
          <Route path="data-quality" element={<DataQualityPage />} />
          <Route path="404" element={<NotFoundPage />} />
          <Route path="*" element={<Navigate to="/404" replace />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;

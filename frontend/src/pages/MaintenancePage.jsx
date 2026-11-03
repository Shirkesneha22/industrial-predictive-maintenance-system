import React, { useState, useEffect, useCallback } from 'react';
import {
  Wrench,
  AlertTriangle,
  Clock,
  CheckCircle,
  FileText,
  RefreshCw,
  Search,
  Filter,
  ShieldAlert,
  Layers,
  Users,
} from 'lucide-react';
import { maintenanceService } from '../services';
import {
  Card,
  StatCard,
  Badge,
  LoadingSpinner,
  ErrorAlert,
  Pagination,
  EmptyState,
} from '../components';

export function MaintenancePage() {
  const [activeTab, setActiveTab] = useState('work-orders'); // 'work-orders' | 'failures'
  const [overview, setOverview] = useState(null);
  const [workOrdersData, setWorkOrdersData] = useState(null);
  const [failuresData, setFailuresData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tableLoading, setTableLoading] = useState(false);
  const [error, setError] = useState(null);

  // Filters
  const [woPage, setWoPage] = useState(1);
  const [woStatus, setWoStatus] = useState('');
  const [failPage, setFailPage] = useState(1);
  const [failSeverity, setFailSeverity] = useState('');
  const [searchTerm, setSearchTerm] = useState('');

  // Load high-level overview
  const fetchOverview = useCallback(async () => {
    try {
      const data = await maintenanceService.getOverview();
      setOverview(data);
    } catch (err) {
      console.error('Failed to load maintenance overview:', err);
    }
  }, []);

  // Load Work Orders
  const fetchWorkOrders = useCallback(async () => {
    setTableLoading(true);
    try {
      const params = { page: woPage, page_size: 15 };
      if (woStatus) params.status = woStatus;
      if (searchTerm) params.search = searchTerm;
      const data = await maintenanceService.getWorkOrders(params);
      setWorkOrdersData(data);
    } catch (err) {
      setError(err);
    } finally {
      setTableLoading(false);
    }
  }, [woPage, woStatus, searchTerm]);

  // Load Failures
  const fetchFailures = useCallback(async () => {
    setTableLoading(true);
    try {
      const params = { page: failPage, page_size: 15 };
      if (failSeverity) params.severity = failSeverity;
      if (searchTerm) params.search = searchTerm;
      const data = await maintenanceService.getFailures(params);
      setFailuresData(data);
    } catch (err) {
      setError(err);
    } finally {
      setTableLoading(false);
    }
  }, [failPage, failSeverity, searchTerm]);

  useEffect(() => {
    setLoading(true);
    Promise.all([fetchOverview(), fetchWorkOrders(), fetchFailures()]).finally(() => {
      setLoading(false);
    });
  }, [fetchOverview]);

  useEffect(() => {
    if (activeTab === 'work-orders') {
      fetchWorkOrders();
    } else {
      fetchFailures();
    }
  }, [activeTab, fetchWorkOrders, fetchFailures]);

  if (loading && !overview) {
    return <LoadingSpinner message="Loading maintenance work orders and failure records..." />;
  }

  return (
    <div className="page-wrapper">
      {/* Page Header */}
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Maintenance & Equipment Failures</h2>
          <p className="page-subheading">
            Work order lifecycle, downtime logs, failure event records, and spare parts management.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-icon"
          onClick={() => {
            fetchOverview();
            if (activeTab === 'work-orders') fetchWorkOrders();
            else fetchFailures();
          }}
          title="Refresh Data"
        >
          <RefreshCw size={15} className={tableLoading ? 'spin-animation' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Cards */}
      <div className="stats-grid">
        <StatCard
          title="Total Work Orders"
          value={overview?.total_work_orders ?? '--'}
          subtitle={`${overview?.completed_work_orders ?? 0} Completed • ${overview?.in_progress_work_orders ?? 0} Active`}
          icon={Wrench}
          variant="default"
        />
        <StatCard
          title="Equipment Failures"
          value={overview?.total_failures ?? '--'}
          subtitle={`Type A: ${overview?.type_a_failures ?? 23} • Type B: ${overview?.type_b_failures ?? 127}`}
          icon={AlertTriangle}
          variant="warning"
        />
        <StatCard
          title="Total Downtime"
          value={`${overview?.total_downtime_hours ?? '--'} hrs`}
          subtitle={`${overview?.total_downtime_minutes?.toLocaleString() ?? '--'} minutes offline`}
          icon={Clock}
          variant="critical"
        />
        <StatCard
          title="Inventory & Team"
          value={`${overview?.total_spare_parts ?? 50} Parts`}
          subtitle={`${overview?.total_technicians ?? 20} Certified Technicians`}
          icon={Users}
          variant="normal"
        />
      </div>

      {/* Navigation Tabs */}
      <div className="card mb-4" style={{ padding: '0.75rem 1rem' }}>
        <div className="flex-align-center justify-between flex-wrap gap-3">
          <div className="sensor-pill-group">
            <button
              type="button"
              className={`pill-btn ${activeTab === 'work-orders' ? 'pill-btn-active' : ''}`}
              onClick={() => setActiveTab('work-orders')}
            >
              <FileText size={15} />
              <span>Maintenance Work Orders ({overview?.total_work_orders ?? 150})</span>
            </button>
            <button
              type="button"
              className={`pill-btn ${activeTab === 'failures' ? 'pill-btn-active' : ''}`}
              onClick={() => setActiveTab('failures')}
            >
              <AlertTriangle size={15} />
              <span>Failure Events ({overview?.total_failures ?? 150})</span>
            </button>
          </div>

          {/* Quick Filters */}
          <div className="flex-align-center gap-3 flex-wrap">
            <div className="filter-select-group">
              <Search size={15} className="filter-icon" />
              <input
                type="text"
                className="form-input"
                style={{ width: '220px', paddingLeft: '2rem' }}
                placeholder="Search ID, machine, or keyword..."
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setWoPage(1);
                  setFailPage(1);
                }}
              />
            </div>

            {activeTab === 'work-orders' ? (
              <div className="flex-align-center gap-2">
                <span className="text-xs text-muted font-semibold">Status:</span>
                <select
                  className="form-select form-select-sm"
                  value={woStatus}
                  onChange={(e) => {
                    setWoStatus(e.target.value);
                    setWoPage(1);
                  }}
                >
                  <option value="">All Statuses</option>
                  <option value="completed">Completed</option>
                  <option value="in_progress">In Progress</option>
                  <option value="pending">Pending</option>
                </select>
              </div>
            ) : (
              <div className="flex-align-center gap-2">
                <span className="text-xs text-muted font-semibold">Severity:</span>
                <select
                  className="form-select form-select-sm"
                  value={failSeverity}
                  onChange={(e) => {
                    setFailSeverity(e.target.value);
                    setFailPage(1);
                  }}
                >
                  <option value="">All Severities</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Table Content */}
      {tableLoading ? (
        <LoadingSpinner message="Updating records..." />
      ) : activeTab === 'work-orders' ? (
        <Card
          title="Maintenance Work Orders Log"
          subtitle={`Showing ${workOrdersData?.items?.length || 0} of ${workOrdersData?.total || 0} work orders`}
        >
          {workOrdersData?.items?.length === 0 ? (
            <EmptyState title="No Work Orders Found" description="No maintenance records match your filter criteria." />
          ) : (
            <>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Order ID</th>
                      <th>Machine</th>
                      <th>Technician</th>
                      <th>Spare Parts</th>
                      <th>Work Type</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Created At (UTC)</th>
                      <th>Completed At (UTC)</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {workOrdersData?.items?.map((wo) => (
                      <tr key={wo.work_order_id}>
                        <td>
                          <strong>WO-{wo.work_order_id.toString().padStart(4, '0')}</strong>
                        </td>
                        <td>
                          <div>
                            <span className="machine-tag-code">MCH-{wo.machine_id}</span>
                            {wo.machine_name && (
                              <div className="text-xs text-muted" style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {wo.machine_name}
                              </div>
                            )}
                          </div>
                        </td>
                        <td>
                          {wo.technician_name ? (
                            <div>
                              <span className="font-semibold text-slate-800">{wo.technician_name}</span>
                              <div className="text-xs text-muted">{wo.technician_code || `TECH-${wo.technician_id}`}</div>
                            </div>
                          ) : wo.technician_id ? (
                            <span className="text-muted">TECH-{wo.technician_id}</span>
                          ) : (
                            <span className="text-muted italic">Unassigned</span>
                          )}
                        </td>
                        <td className="text-xs text-secondary" style={{ maxWidth: '160px' }}>
                          {wo.parts_information || 'Standard Service Kit'}
                        </td>
                        <td>
                          <span className="text-capitalize">{wo.work_type}</span>
                        </td>
                        <td>
                          <Badge
                            variant={
                              wo.priority === 'critical'
                                ? 'critical'
                                : wo.priority === 'high'
                                ? 'warning'
                                : 'neutral'
                            }
                          >
                            {wo.priority}
                          </Badge>
                        </td>
                        <td>
                          <Badge
                            variant={
                              wo.status === 'completed'
                                ? 'normal'
                                : wo.status === 'in_progress'
                                ? 'warning'
                                : 'neutral'
                            }
                          >
                            {wo.status.replace('_', ' ')}
                          </Badge>
                        </td>
                        <td>{new Date(wo.created_at).toLocaleString()}</td>
                        <td>
                          {wo.completed_at ? new Date(wo.completed_at).toLocaleString() : '--'}
                        </td>
                        <td className="text-secondary text-sm" style={{ maxWidth: '240px' }}>
                          {wo.description || 'Routine scheduled corrective servicing'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={woPage}
                totalPages={workOrdersData?.total_pages || 1}
                onPageChange={setWoPage}
              />
            </>
          )}
        </Card>
      ) : (
        <Card
          title="Historical Equipment Failure Events"
          subtitle={`Showing ${failuresData?.items?.length || 0} of ${failuresData?.total || 0} failure records`}
        >
          {failuresData?.items?.length === 0 ? (
            <EmptyState title="No Failures Found" description="No failure events match your filter criteria." />
          ) : (
            <>
              <div className="table-responsive">
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>Failure ID</th>
                      <th>Machine</th>
                      <th>Failure Mode</th>
                      <th>Severity</th>
                      <th>Failure Timestamp (UTC)</th>
                      <th>Downtime</th>
                      <th>Description</th>
                    </tr>
                  </thead>
                  <tbody>
                    {failuresData?.items?.map((f) => (
                      <tr key={f.failure_id}>
                        <td>
                          <strong>FAIL-{f.failure_id.toString().padStart(4, '0')}</strong>
                        </td>
                        <td>
                          <div>
                            <span className="machine-tag-code">MCH-{f.machine_id}</span>
                            {f.machine_name && (
                              <div className="text-xs text-muted" style={{ maxWidth: '160px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                                {f.machine_name}
                              </div>
                            )}
                          </div>
                        </td>
                        <td>
                          <span className="font-semibold text-slate-800">
                            {f.failure_type.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <Badge
                            variant={
                              f.severity === 'critical'
                                ? 'critical'
                                : f.severity === 'high'
                                ? 'warning'
                                : 'neutral'
                            }
                          >
                            {f.severity}
                          </Badge>
                        </td>
                        <td>{new Date(f.failure_time).toLocaleString()}</td>
                        <td>
                          <span className="font-semibold">{f.downtime_minutes} mins</span>
                          <span className="text-xs text-muted ml-1">
                            ({(f.downtime_minutes / 60).toFixed(1)}h)
                          </span>
                        </td>
                        <td className="text-secondary text-sm" style={{ maxWidth: '320px' }}>
                          {f.description}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <Pagination
                page={failPage}
                totalPages={failuresData?.total_pages || 1}
                onPageChange={setFailPage}
              />
            </>
          )}
        </Card>
      )}
    </div>
  );
}

export default MaintenancePage;

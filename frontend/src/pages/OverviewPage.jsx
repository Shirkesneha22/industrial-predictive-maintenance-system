import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  AlertTriangle,
  CheckCircle,
  Activity,
  Cpu,
  ShieldAlert,
  ArrowRight,
  TrendingDown,
  TrendingUp,
  Radio,
  RefreshCw,
  SlidersHorizontal,
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { predictionService } from '../services';
import {
  Card,
  StatCard,
  Badge,
  LoadingSpinner,
  ErrorAlert,
  EmptyState,
} from '../components';

const RISK_COLORS = {
  Normal: '#16a34a', // Emerald Green
  Warning: '#f59e0b', // Amber
  Critical: '#dc2626', // Bright Crimson
};

export const PRODUCTION_LINES = [
  { id: 25, code: 'LINE-PUN-01', name: 'Line 25 - Chassis Fabrication' },
  { id: 26, code: 'LINE-PUN-02', name: 'Line 26 - Powertrain Machining' },
  { id: 27, code: 'LINE-PUN-03', name: 'Line 27 - CNC Milling & Turning' },
  { id: 28, code: 'LINE-PUN-04', name: 'Line 28 - Robotic Welding & Stamping' },
  { id: 29, code: 'LINE-CHN-01', name: 'Line 29 - Hydraulic Stamping' },
  { id: 30, code: 'LINE-CHN-02', name: 'Line 30 - Turbine & Impeller' },
  { id: 31, code: 'LINE-CHN-03', name: 'Line 31 - Heat Treatment' },
  { id: 32, code: 'LINE-CHN-04', name: 'Line 32 - Heavy Plate Bending' },
  { id: 33, code: 'LINE-AMD-01', name: 'Line 33 - Pump Assembly' },
  { id: 34, code: 'LINE-AMD-02', name: 'Line 34 - Compressor & Blower' },
  { id: 35, code: 'LINE-AMD-03', name: 'Line 35 - Hydraulic Valve Cell' },
  { id: 36, code: 'LINE-AMD-04', name: 'Line 36 - Polymer Extrusion' },
];

export function OverviewPage() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lineFilter, setLineFilter] = useState('');

  const fetchOverviewData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: 1,
        page_size: 100, // Fetch up to 100 machines for fleet summary and anomaly ranking
      };
      if (lineFilter) {
        params.line_id = Number(lineFilter);
      }
      const response = await predictionService.getFleetAnomalies(params);
      setData(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [lineFilter]);

  useEffect(() => {
    fetchOverviewData();
  }, [fetchOverviewData]);

  if (loading && !data) {
    return <LoadingSpinner message="Calculating fleet risk distribution and active anomalies..." />;
  }

  if (error && !data) {
    return (
      <ErrorAlert
        title="Failed to Load Fleet Overview"
        message={error}
        onRetry={fetchOverviewData}
      />
    );
  }

  const summary = data?.summary || {
    total_machines_evaluated: 0,
    normal_count: 0,
    warning_count: 0,
    critical_count: 0,
    correlated_degradation_count: 0,
    isolated_sensor_fault_count: 0,
  };

  const items = data?.items || [];

  // Filter critical machines for active alert banner
  const criticalMachines = items.filter((item) => item.risk_level === 'Critical');

  // Filter recent anomalous machines (Warning, Critical, or isolated faults)
  const anomalousMachines = items.filter(
    (item) => item.risk_level !== 'Normal' || item.has_isolated_sensor_fault
  );

  // Compute fleet-wide average sensor reliability index
  const avgSensorReliability =
    items.length > 0
      ? (
          items.reduce((acc, m) => acc + (m.sensor_reliability_index || 100), 0) /
          items.length
        ).toFixed(1)
      : '100.0';

  // Pie chart data: Normal vs Warning vs Critical
  const riskDistributionData = [
    { name: 'Normal', value: summary.normal_count, color: RISK_COLORS.Normal },
    { name: 'Warning', value: summary.warning_count, color: RISK_COLORS.Warning },
    { name: 'Critical', value: summary.critical_count, color: RISK_COLORS.Critical },
  ].filter((d) => d.value > 0);

  // Bar chart data for degradation mode breakdown
  const conditionBreakdownData = [
    {
      category: 'Operating Status',
      Normal: summary.normal_count,
      Warning: summary.warning_count,
      Critical: summary.critical_count,
    },
    {
      category: 'Diagnostic Flags',
      'Correlated Wear': summary.correlated_degradation_count,
      'Sensor Faults': summary.isolated_sensor_fault_count,
    },
  ];

  return (
    <div className="page-wrapper">
      {/* Page Header and Controls */}
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Equipment Fleet Status</h2>
          <p className="page-subheading">
            Continuous health telemetry and risk ranking across monitored assets.
          </p>
        </div>
        <div className="page-controls">
          <div className="filter-select-group">
            <SlidersHorizontal size={16} className="filter-icon" />
            <select
              className="form-select"
              value={lineFilter}
              onChange={(e) => setLineFilter(e.target.value)}
              aria-label="Filter by Production Line"
            >
              <option value="">All Production Lines</option>
              {PRODUCTION_LINES.map((line) => (
                <option key={line.id} value={line.id}>
                  {line.name} ({line.code})
                </option>
              ))}
            </select>
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-icon"
            onClick={fetchOverviewData}
            title="Refresh Fleet Data"
          >
            <RefreshCw size={15} className={loading ? 'spin-animation' : ''} />
            <span>Refresh</span>
          </button>
        </div>
      </div>

      {/* Fleet Topology Overview Cards */}
      <div className="card mb-4" style={{ padding: '1rem 1.25rem', background: '#f8fafc', border: '1px solid #e2e8f0' }}>
        <div className="flex-align-center justify-between flex-wrap gap-3">
          <div className="flex-align-center gap-4 flex-wrap">
            <div>
              <span className="text-xs text-muted font-bold text-uppercase" style={{ letterSpacing: '0.05em' }}>Plants</span>
              <div className="font-bold text-slate-800" style={{ fontSize: '1.25rem' }}>{summary.total_plants || 3} Manufacturing Hubs</div>
            </div>
            <div style={{ width: 1, height: 32, background: '#cbd5e1' }} />
            <div>
              <span className="text-xs text-muted font-bold text-uppercase" style={{ letterSpacing: '0.05em' }}>Lines</span>
              <div className="font-bold text-slate-800" style={{ fontSize: '1.25rem' }}>{summary.total_lines || 12} Production Lines</div>
            </div>
            <div style={{ width: 1, height: 32, background: '#cbd5e1' }} />
            <div>
              <span className="text-xs text-muted font-bold text-uppercase" style={{ letterSpacing: '0.05em' }}>Equipment</span>
              <div className="font-bold text-slate-800" style={{ fontSize: '1.25rem' }}>{summary.total_machines_evaluated || 100} Machines</div>
            </div>
            <div style={{ width: 1, height: 32, background: '#cbd5e1' }} />
            <div>
              <span className="text-xs text-muted font-bold text-uppercase" style={{ letterSpacing: '0.05em' }}>IoT Telemetry</span>
              <div className="font-bold text-slate-800" style={{ fontSize: '1.25rem' }}>{summary.total_sensors || 500} Mounted Sensors</div>
            </div>
          </div>

          <div>
            <div className="badge badge-normal" style={{ fontSize: '0.85rem', padding: '0.4rem 0.75rem' }}>
              Overall Machine Health: <strong>{(summary.average_health_index || 84.8).toFixed(1)} / 100</strong>
            </div>
          </div>
        </div>
      </div>

      {/* KPI Metric Cards */}
      <div className="stats-grid">
        <StatCard
          title="Monitored Assets"
          value={summary.total_machines_evaluated}
          subtitle="Active fleet equipment"
          icon={Cpu}
          variant="default"
        />
        <StatCard
          title="Normal Condition"
          value={summary.normal_count}
          subtitle={`${summary.total_machines_evaluated ? ((summary.normal_count / summary.total_machines_evaluated) * 100).toFixed(0) : 0}% of fleet operational`}
          icon={CheckCircle}
          variant="normal"
        />
        <StatCard
          title="Warning Condition"
          value={summary.warning_count}
          subtitle="Early degradation observed"
          icon={AlertTriangle}
          variant="warning"
        />
        <StatCard
          title="Critical Alerts"
          value={summary.critical_count}
          subtitle="Immediate service required"
          icon={ShieldAlert}
          variant="critical"
        />
        <StatCard
          title="Sensor Reliability"
          value={`${avgSensorReliability}%`}
          subtitle={`${summary.isolated_sensor_fault_count} isolated sensor faults`}
          icon={Radio}
          variant={Number(avgSensorReliability) >= 95 ? 'normal' : 'warning'}
        />
      </div>

      {/* Critical Machine Urgent Alerts Panel */}
      {criticalMachines.length > 0 && (
        <div className="critical-alerts-banner">
          <div className="critical-alerts-header">
            <div className="critical-icon-wrapper">
              <ShieldAlert size={22} />
            </div>
            <div>
              <h3 className="critical-banner-title">
                Critical Equipment Degradation Detected ({criticalMachines.length}{' '}
                {criticalMachines.length === 1 ? 'Machine' : 'Machines'})
              </h3>
              <p className="critical-banner-desc">
                The physics risk engine detected multi-sensor correlated degradation requiring immediate maintenance intervention.
              </p>
            </div>
          </div>

          <div className="critical-machines-grid">
            {criticalMachines.map((m) => (
              <div key={m.machine_id} className="critical-machine-card">
                <div className="critical-machine-top">
                  <div>
                    <span className="critical-machine-code">{m.machine_code}</span>
                    <span className="critical-machine-name">{m.machine_name}</span>
                  </div>
                  <Badge variant="critical">Risk: {m.risk_score.toFixed(1)}</Badge>
                </div>

                <div className="critical-metric-row">
                  <div>
                    <span className="metric-label">Health Index</span>
                    <span className="metric-val text-critical">
                      {m.health_index.toFixed(1)} / 100
                    </span>
                  </div>
                  <div>
                    <span className="metric-label">Diagnosed Failure</span>
                    <span className="metric-val font-medium">
                      {m.dominant_failure_mode ? m.dominant_failure_mode.replace('_', ' ') : 'General Wear'}
                    </span>
                  </div>
                </div>

                <div className="critical-action-box">
                  <strong>Recommended Action:</strong> {m.recommended_action}
                </div>

                <Link to={`/machines/${m.machine_id}`} className="critical-view-link">
                  <span>Open Diagnostic Breakdown</span>
                  <ArrowRight size={14} />
                </Link>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Risk Distribution Visualizations */}
      <div className="grid-2-col">
        <Card
          title="Fleet Risk Distribution"
          subtitle="Proportion of machines classified by severity index"
        >
          {riskDistributionData.length > 0 ? (
            <div className="chart-container" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={riskDistributionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, value, percent }) =>
                      `${name}: ${value} (${(percent * 100).toFixed(0)}%)`
                    }
                  >
                    {riskDistributionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val, name) => [`${val} machines`, name]}
                    contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState description="No machine risk data available." />
          )}
        </Card>

        <Card
          title="Wear vs Instrumentation Diagnosis"
          subtitle="Distinguishing physical degradation from single-sensor faults"
        >
          <div className="chart-container" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={conditionBreakdownData}
                margin={{ top: 20, right: 30, left: 10, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="category" stroke="#64748b" />
                <YAxis allowDecimals={false} stroke="#64748b" />
                <Tooltip
                  contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1' }}
                />
                <Legend verticalAlign="bottom" height={36} />
                <Bar dataKey="Normal" fill="#16a34a" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Warning" fill="#f59e0b" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Critical" fill="#dc2626" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Correlated Wear" fill="#8b5cf6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Sensor Faults" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Recent Fleet Anomalies Table */}
      <Card
        title="Detected Machine Anomalies & Point-in-Time Risk"
        subtitle="Ranked in order of highest degradation risk score"
        action={
          <Link to="/machines" className="btn btn-outline btn-sm">
            <span>View All Machines</span>
            <ArrowRight size={14} />
          </Link>
        }
      >
        {anomalousMachines.length === 0 ? (
          <EmptyState
            title="All Monitored Machines Normal"
            description="No active anomalies or elevated risk levels detected in the fleet."
            icon={CheckCircle}
          />
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Machine</th>
                  <th>Type</th>
                  <th>Production Line</th>
                  <th>Health Index</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Anomaly Type</th>
                  <th>Dominant Failure Mode</th>
                  <th>Sensor Reliability</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {anomalousMachines.slice(0, 10).map((machine) => (
                  <tr key={machine.machine_id}>
                    <td>
                      <div className="cell-title">{machine.machine_code}</div>
                      <div className="cell-sub">{machine.machine_name}</div>
                    </td>
                    <td>{machine.machine_type}</td>
                    <td>Line {machine.line_id}</td>
                    <td>
                      <div className="health-bar-container">
                        <span className="health-bar-text">
                          {machine.health_index.toFixed(1)}%
                        </span>
                        <div className="health-progress-bg">
                          <div
                            className={`health-progress-fill ${
                              machine.health_index >= 70
                                ? 'bg-normal'
                                : machine.health_index >= 40
                                ? 'bg-warning'
                                : 'bg-critical'
                            }`}
                            style={{ width: `${Math.max(5, machine.health_index)}%` }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="font-semibold">{machine.risk_score.toFixed(1)}</span>
                    </td>
                    <td>
                      <Badge variant={machine.risk_level.toLowerCase()}>
                        {machine.risk_level}
                      </Badge>
                    </td>
                    <td>
                      {machine.has_correlated_degradation && (
                        <span className="pill-badge pill-purple" title="Multi-sensor wear detected">
                          Correlated Wear
                        </span>
                      )}
                      {machine.has_isolated_sensor_fault && (
                        <span className="pill-badge pill-blue" title="Single sensor fault isolated">
                          Sensor Fault
                        </span>
                      )}
                      {!machine.has_correlated_degradation && !machine.has_isolated_sensor_fault && (
                        <span className="text-muted">Standard</span>
                      )}
                    </td>
                    <td>
                      {machine.dominant_failure_mode ? (
                        <span className="font-medium text-capitalize">
                          {machine.dominant_failure_mode.replace('_', ' ')}
                        </span>
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td>
                      <span
                        className={
                          machine.sensor_reliability_index < 90
                            ? 'text-warning font-medium'
                            : 'text-muted'
                        }
                      >
                        {machine.sensor_reliability_index.toFixed(0)}%
                      </span>
                    </td>
                    <td className="text-right">
                      <Link
                        to={`/machines/${machine.machine_id}`}
                        className="btn btn-outline btn-xs"
                      >
                        Details
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </div>
  );
}

export default OverviewPage;

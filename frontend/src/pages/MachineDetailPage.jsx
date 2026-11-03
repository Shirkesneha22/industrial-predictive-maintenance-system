import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  ArrowLeft,
  RefreshCw,
  Cpu,
  Radio,
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  ShieldCheck,
  Zap,
  Info,
} from 'lucide-react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import {
  machineService,
  predictionService,
  telemetryService,
} from '../services';
import {
  Card,
  StatCard,
  Badge,
  LoadingSpinner,
  ErrorAlert,
  EmptyState,
} from '../components';

const SENSOR_COLORS = {
  vibration: '#8b5cf6', // Violet
  temperature: '#ef4444', // Red
  acoustic: '#06b6d4', // Cyan
  pressure: '#f59e0b', // Amber
  current: '#10b981', // Emerald
};

/**
 * Resolves sensor status using existing backend classification fields.
 * Distinguishes Nominal, Sensor Fault, Isolated Anomaly, and Correlated Degradation.
 */
function getSignalStatus(signal) {
  if (signal.is_fault || signal.explanation?.includes('[Instrumentation Reliability Warning]')) {
    return { label: 'Sensor Fault', className: 'pill-badge pill-red' };
  }
  if (signal.explanation?.includes('[Correlated Machine Degradation]') || signal.risk_contribution > 0) {
    return { label: 'Correlated Degradation', className: 'pill-badge pill-purple' };
  }
  if (signal.explanation?.includes('[Isolated Sensor Anomaly]')) {
    return { label: 'Isolated Anomaly', className: 'pill-badge pill-yellow' };
  }
  return { label: 'Nominal', className: 'pill-badge pill-green' };
}

export function MachineDetailPage() {
  const { id } = useParams();
  const machineId = Number(id);

  const [machine, setMachine] = useState(null);
  const [riskAssessment, setRiskAssessment] = useState(null);
  const [rulData, setRulData] = useState(null);
  const [latestTelemetry, setLatestTelemetry] = useState([]);
  const [historicalTelemetry, setHistoricalTelemetry] = useState([]);
  const [selectedSensorType, setSelectedSensorType] = useState('all');
  const [maintenanceHistory, setMaintenanceHistory] = useState(null);

  const [loading, setLoading] = useState(true);
  const [telemetryLoading, setTelemetryLoading] = useState(false);
  const [error, setError] = useState(null);

  // Load Machine details, Risk evaluation, RUL, Latest readings, and Maintenance history
  const loadMachineData = useCallback(async () => {
    if (!machineId) return;
    setLoading(true);
    setError(null);
    try {
      const [mRes, rRes, rulRes, latestRes, maintRes] = await Promise.all([
        machineService.getMachineById(machineId),
        machineService.getMachineRisk(machineId),
        predictionService.getMachineRul(machineId),
        telemetryService.getLatestTelemetry(machineId),
        machineService.getMachineMaintenance(machineId).catch(() => null),
      ]);

      setMachine(mRes);
      setRiskAssessment(rRes);
      setRulData(rulRes);
      setLatestTelemetry(latestRes || []);
      setMaintenanceHistory(maintRes);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [machineId]);

  // Load Historical Telemetry (defaulting to 100 recent points)
  const loadTelemetryStream = useCallback(async () => {
    if (!machineId) return;
    setTelemetryLoading(true);
    try {
      const params = {
        machine_id: machineId,
        page_size: 100,
        page: 1,
      };
      if (selectedSensorType !== 'all') {
        params.sensor_type = selectedSensorType;
      }
      const response = await telemetryService.getHistoricalTelemetry(params);
      setHistoricalTelemetry(response.items || []);
    } catch (err) {
      console.error('Failed to load telemetry stream:', err);
    } finally {
      setTelemetryLoading(false);
    }
  }, [machineId, selectedSensorType]);

  useEffect(() => {
    loadMachineData();
  }, [loadMachineData]);

  useEffect(() => {
    loadTelemetryStream();
  }, [loadTelemetryStream]);

  // Transform historical telemetry into chart data points sorted chronologically
  const chartData = useMemo(() => {
    if (!historicalTelemetry.length) return [];
    // Sort ascending by recorded_at for chronological line graph
    const sorted = [...historicalTelemetry].sort(
      (a, b) => new Date(a.recorded_at).getTime() - new Date(b.recorded_at).getTime()
    );

    // Group or map entries
    return sorted.map((item) => ({
      timestamp: new Date(item.recorded_at).toLocaleTimeString([], {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
      }),
      isoTime: item.recorded_at,
      value:
        item.quality_status === 'missing' || item.quality_status === 'invalid'
          ? null
          : item.value !== null
          ? Number(item.value.toFixed(2))
          : null,
      sensor: item.sensor_code || `Sensor-${item.sensor_id}`,
      type: item.sensor_type,
      unit: item.unit || '',
      quality: item.quality_status,
    }));
  }, [historicalTelemetry]);

  // Available sensor types on this machine
  const availableSensorTypes = useMemo(() => {
    if (!machine?.sensors) return [];
    const types = new Set(machine.sensors.map((s) => s.sensor_type));
    return Array.from(types);
  }, [machine]);

  if (loading && !machine) {
    return <LoadingSpinner message={`Loading diagnostics for Machine #${machineId}...`} />;
  }

  if (error && !machine) {
    return (
      <div className="page-wrapper">
        <Link to="/machines" className="btn btn-outline btn-sm mb-4">
          <ArrowLeft size={15} />
          <span>Back to Equipment Fleet</span>
        </Link>
        <ErrorAlert
          title="Failed to Load Machine Details"
          message={error}
          onRetry={loadMachineData}
        />
      </div>
    );
  }

  return (
    <div className="page-wrapper">
      {/* Top Navigation & Header */}
      <div className="page-header-row">
        <div className="flex-align-center gap-3">
          <Link to="/machines" className="btn btn-outline btn-sm" aria-label="Back">
            <ArrowLeft size={16} />
            <span>Machines</span>
          </Link>
          <div>
            <div className="flex-align-center gap-2">
              <h2 className="page-heading mb-0">{machine.name}</h2>
              <span className="machine-tag-code">{machine.machine_code}</span>
              <Badge variant={machine.is_active ? 'success' : 'neutral'}>
                {machine.is_active ? 'Active' : 'Offline'}
              </Badge>
            </div>
            <p className="page-subheading">
              {machine.machine_type} • Line {machine.line_id} • Manufacturer:{' '}
              {machine.manufacturer || 'Standard Industrial OEM'}
            </p>
          </div>
        </div>

        <button
          type="button"
          className="btn btn-secondary btn-icon"
          onClick={() => {
            loadMachineData();
            loadTelemetryStream();
          }}
          title="Refresh Machine Telemetry"
        >
          <RefreshCw size={15} className={loading || telemetryLoading ? 'spin-animation' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Point-in-time Risk & Health Summary Cards */}
      <div className="stats-grid">
        <StatCard
          title="Machine Health Index"
          value={`${riskAssessment ? riskAssessment.health_index.toFixed(1) : '--'} / 100`}
          subtitle="Physics condition score"
          icon={Activity}
          variant={
            riskAssessment?.health_index >= 70
              ? 'normal'
              : riskAssessment?.health_index >= 40
              ? 'warning'
              : 'critical'
          }
        />
        <StatCard
          title="Degradation Risk Score"
          value={`${riskAssessment ? riskAssessment.risk_score.toFixed(1) : '--'} / 100`}
          subtitle="Anti-leakage physics assessment"
          icon={AlertTriangle}
          variant={
            riskAssessment?.risk_level === 'Critical'
              ? 'critical'
              : riskAssessment?.risk_level === 'Warning'
              ? 'warning'
              : 'normal'
          }
        />
        <StatCard
          title="Risk Classification"
          value={riskAssessment ? riskAssessment.risk_level : '--'}
          subtitle={
            riskAssessment?.has_correlated_degradation
              ? 'Multi-sensor degradation'
              : riskAssessment?.has_isolated_sensor_fault
              ? 'Isolated sensor fault'
              : 'Nominal operational envelope'
          }
          icon={ShieldCheck}
          variant={riskAssessment?.risk_level?.toLowerCase() || 'default'}
        />
        <StatCard
          title="Sensor Reliability"
          value={`${riskAssessment ? riskAssessment.sensor_reliability_index.toFixed(0) : '--'}%`}
          subtitle={`${machine?.sensors?.length || 0} mounted IoT channels`}
          icon={Radio}
          variant={
            riskAssessment?.sensor_reliability_index >= 90 ? 'normal' : 'warning'
          }
        />
      </div>

      {/* Physics Condition & Contextual Maintenance Recommendation Banner */}
      {riskAssessment && (
        <Card
          className={`assessment-banner ${
            riskAssessment.risk_level === 'Critical'
              ? 'border-critical-left'
              : riskAssessment.risk_level === 'Warning'
              ? 'border-warning-left'
              : 'border-normal-left'
          }`}
        >
          <div className="banner-grid">
            <div>
              <div className="flex-align-center gap-2 mb-2">
                <Zap size={18} className="text-primary" />
                <h4 className="font-semibold text-slate-800">
                  Diagnostic Condition & Maintenance Protocol
                </h4>
              </div>
              <p className="text-secondary mb-3">
                {riskAssessment.explanation_summary ||
                  'All monitored physical vibration, acoustic, and thermal telemetry vectors are within baseline limits.'}
              </p>
              <div className="action-highlight-box">
                <span className="action-title">Actionable Recommendation:</span>
                <span className="action-body">{riskAssessment.recommended_action}</span>
              </div>
            </div>

            <div className="banner-side-metrics">
              <div className="side-metric-item">
                <span className="side-label">Dominant Failure Mode</span>
                <span className="side-val text-capitalize font-semibold">
                  {riskAssessment.dominant_failure_mode
                    ? riskAssessment.dominant_failure_mode.replace('_', ' ')
                    : 'None Diagnosed'}
                </span>
              </div>
              <div className="side-metric-item">
                <span className="side-label">Diagnostic Confidence</span>
                <span className="side-val">
                  {(riskAssessment.failure_mode_confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="side-metric-item">
                <span className="side-label">Anti-Leakage Calibration</span>
                <span className="side-val text-muted text-xs">
                  {riskAssessment.is_calibrated_probability
                    ? 'Calibrated'
                    : 'Engineering Indicator (Strict Anti-Leakage)'}
                </span>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* Remaining Useful Life (RUL) Anti-Leakage Notice Card */}
      <Card className="rul-anti-leakage-card">
        <div className="flex-align-center gap-3">
          <div className="info-icon-badge">
            <Info size={20} />
          </div>
          <div className="flex-1">
            <h4 className="font-semibold text-slate-800 mb-1">
              Remaining Useful Life (RUL) Status
            </h4>
            <p className="text-sm text-secondary mb-0">
              {rulData?.message ||
                'Unvalidated RUL is not claimed under anti-leakage guidelines.'}
            </p>
          </div>
          <div>
            <span className="badge badge-neutral">
              {rulData?.remaining_useful_life_hours !== null && rulData?.remaining_useful_life_hours !== undefined
                ? `${rulData.remaining_useful_life_hours} hrs`
                : 'RUL Uncalibrated (Anti-Leakage)'}
            </span>
          </div>
        </div>
      </Card>

      {/* Sensor Topology and Latest Telemetry */}
      <Card
        title="Mounted Sensor Topology & Real-Time Readings"
        subtitle="Latest telemetry captured per active sensor channel"
      >
        <div className="sensors-grid">
          {machine?.sensors?.map((sensor) => {
            const latest = latestTelemetry.find((t) => t.sensor_id === sensor.sensor_id);
            const contributingSignal = riskAssessment?.contributing_signals?.find(
              (s) => s.sensor_id === sensor.sensor_id
            );

            return (
              <div key={sensor.sensor_id} className="sensor-card">
                <div className="sensor-card-top">
                  <div>
                    <span className="sensor-code">{sensor.sensor_code}</span>
                    <span className="sensor-type">{sensor.sensor_type}</span>
                  </div>
                  {latest && (
                    <Badge variant={latest.quality_status}>
                      {latest.quality_status}
                    </Badge>
                  )}
                </div>

                <div className="sensor-value-box">
                  <div className="sensor-value-num">
                    {latest?.quality_status === 'missing'
                      ? 'N/A (Missing)'
                      : latest?.quality_status === 'invalid'
                      ? 'Invalid'
                      : latest?.value !== null && latest?.value !== undefined
                      ? latest.value.toFixed(2)
                      : '--'}
                  </div>
                  <span className="sensor-unit">{sensor.unit}</span>
                </div>

                {contributingSignal && (
                  <div className="sensor-signal-meta">
                    <div className="signal-item">
                      <span>Baseline:</span>
                      <strong>{contributingSignal.nominal_baseline.toFixed(1)}</strong>
                    </div>
                    <div className="signal-item">
                      <span>Z-Score:</span>
                      <strong
                        className={
                          Math.abs(contributingSignal.z_score) >= 3
                            ? 'text-critical'
                            : Math.abs(contributingSignal.z_score) >= 2
                            ? 'text-warning'
                            : 'text-normal'
                        }
                      >
                        {contributingSignal.z_score.toFixed(2)}σ
                      </strong>
                    </div>
                    <div className="signal-item">
                      <span>Risk Contribution:</span>
                      <strong>
                        {contributingSignal.risk_contribution.toFixed(1)}%
                      </strong>
                    </div>
                  </div>
                )}

                <div className="sensor-card-footer">
                  <Clock size={12} />
                  <span>
                    {latest?.recorded_at
                      ? new Date(latest.recorded_at).toLocaleTimeString()
                      : 'No signal'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </Card>

      {/* Telemetry Time-Series Chart */}
      <Card
        title="Sensor Telemetry Time-Series"
        subtitle="Recent historical data stream (adhering to database query limits)"
        action={
          <div className="chart-filters-row">
            <span className="filter-label">Filter Channel:</span>
            <div className="sensor-pill-group">
              <button
                type="button"
                className={`pill-btn ${selectedSensorType === 'all' ? 'pill-btn-active' : ''}`}
                onClick={() => setSelectedSensorType('all')}
              >
                All Channels
              </button>
              {availableSensorTypes.map((type) => (
                <button
                  key={type}
                  type="button"
                  className={`pill-btn ${selectedSensorType === type ? 'pill-btn-active' : ''}`}
                  onClick={() => setSelectedSensorType(type)}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>
        }
      >
        {telemetryLoading ? (
          <div className="chart-loading-box">
            <LoadingSpinner inline message="Fetching historical telemetry stream..." />
          </div>
        ) : chartData.length === 0 ? (
          <EmptyState
            title="No Telemetry Data Found"
            description="No recent sensor telemetry records were returned for this machine."
          />
        ) : (
          <div className="chart-container" style={{ height: 350 }}>
            <ResponsiveContainer width="100%" height="100%">
              <LineChart
                data={chartData}
                margin={{ top: 15, right: 30, left: 10, bottom: 25 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis
                  dataKey="timestamp"
                  stroke="#64748b"
                  angle={-25}
                  textAnchor="end"
                  height={50}
                  tick={{ fontSize: 11 }}
                />
                <YAxis stroke="#64748b" />
                <Tooltip
                  formatter={(val, name, props) => [
                    `${val} ${props.payload.unit}`,
                    `${props.payload.sensor} (${props.payload.type})`,
                  ]}
                  labelFormatter={(lbl, items) => {
                    if (items && items[0]) {
                      return `Time: ${lbl} (Quality: ${items[0].payload.quality})`;
                    }
                    return `Time: ${lbl}`;
                  }}
                  contentStyle={{
                    borderRadius: '6px',
                    border: '1px solid #cbd5e1',
                    fontSize: '12px',
                  }}
                />
                <Legend verticalAlign="top" height={36} />
                <Line
                  type="monotone"
                  dataKey="value"
                  name="Observed Reading"
                  stroke="#2563eb"
                  strokeWidth={2}
                  dot={{ r: 2 }}
                  activeDot={{ r: 5 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </Card>

      {/* Contributing Signals Detail Table */}
      {riskAssessment?.contributing_signals?.length > 0 && (
        <Card
          title="Contributing Sensor Signals Breakdown"
          subtitle="Physics-informed weights and anomaly indicators per channel"
        >
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Sensor Code</th>
                  <th>Channel Type</th>
                  <th>Observed Mean</th>
                  <th>Nominal Baseline</th>
                  <th>Z-Score</th>
                  <th>Trend Slope</th>
                  <th>Weight</th>
                  <th>Risk Contribution</th>
                  <th>Instrumentation Status</th>
                  <th>Diagnostic Explanation</th>
                </tr>
              </thead>
              <tbody>
                {riskAssessment.contributing_signals.map((signal) => (
                  <tr key={signal.sensor_id}>
                    <td>
                      <span className="font-semibold">{signal.sensor_code}</span>
                    </td>
                    <td>
                      <span className="text-secondary">{signal.sensor_type}</span>
                    </td>
                    <td>
                      {signal.observed_mean !== null
                        ? signal.observed_mean.toFixed(2)
                        : '--'}
                    </td>
                    <td>{signal.nominal_baseline.toFixed(2)}</td>
                    <td>
                      <span
                        className={
                          Math.abs(signal.z_score) >= 3
                            ? 'text-critical font-bold'
                            : Math.abs(signal.z_score) >= 2
                            ? 'text-warning font-semibold'
                            : 'text-normal'
                        }
                      >
                        {signal.z_score.toFixed(2)}σ
                      </span>
                    </td>
                    <td>{signal.trend_slope.toFixed(4)}</td>
                    <td>{(signal.weight * 100).toFixed(0)}%</td>
                    <td>
                      <span className="font-semibold">
                        {signal.risk_contribution.toFixed(1)}%
                      </span>
                    </td>
                    <td>
                      {(() => {
                        const status = getSignalStatus(signal);
                        return <span className={status.className}>{status.label}</span>;
                      })()}
                    </td>
                    <td>
                      <span className="text-sm text-secondary">
                        {signal.explanation}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}

      {/* Machine Maintenance & Failure History */}
      <Card
        title="Maintenance History & Incident Records"
        subtitle={`Historical corrective work orders and failure records for ${machine?.name}`}
      >
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {/* Work Orders */}
          <div>
            <h4 className="font-semibold text-slate-800 mb-3" style={{ fontSize: '0.95rem' }}>
              Logged Work Orders ({maintenanceHistory?.work_orders?.length || 0})
            </h4>
            {(!maintenanceHistory?.work_orders || maintenanceHistory.work_orders.length === 0) ? (
              <p className="text-sm text-muted">No corrective maintenance work orders recorded for this unit.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table" style={{ fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th>Order</th>
                      <th>Type</th>
                      <th>Priority</th>
                      <th>Status</th>
                      <th>Date</th>
                    </tr>
                  </thead>
                  <tbody>
                    {maintenanceHistory.work_orders.map((wo) => (
                      <tr key={wo.work_order_id}>
                        <td><strong>WO-{wo.work_order_id}</strong></td>
                        <td className="text-capitalize">{wo.work_type}</td>
                        <td>
                          <Badge variant={wo.priority === 'critical' ? 'critical' : wo.priority === 'high' ? 'warning' : 'neutral'}>
                            {wo.priority}
                          </Badge>
                        </td>
                        <td>
                          <Badge variant={wo.status === 'completed' ? 'normal' : 'warning'}>
                            {wo.status}
                          </Badge>
                        </td>
                        <td>{new Date(wo.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Failure Events */}
          <div>
            <h4 className="font-semibold text-slate-800 mb-3" style={{ fontSize: '0.95rem' }}>
              Recorded Failure Events ({maintenanceHistory?.failures?.length || 0})
            </h4>
            {(!maintenanceHistory?.failures || maintenanceHistory.failures.length === 0) ? (
              <p className="text-sm text-muted">No unpredicted equipment failures logged during the 90-day window.</p>
            ) : (
              <div className="table-responsive">
                <table className="data-table" style={{ fontSize: '0.8rem' }}>
                  <thead>
                    <tr>
                      <th>Failure</th>
                      <th>Mode</th>
                      <th>Severity</th>
                      <th>Downtime</th>
                      <th>Timestamp</th>
                    </tr>
                  </thead>
                  <tbody>
                    {maintenanceHistory.failures.map((f) => (
                      <tr key={f.failure_id}>
                        <td><strong>FAIL-{f.failure_id}</strong></td>
                        <td>{f.failure_type.replace('_', ' ')}</td>
                        <td>
                          <Badge variant={f.severity === 'critical' ? 'critical' : 'warning'}>
                            {f.severity}
                          </Badge>
                        </td>
                        <td>{f.downtime_minutes}m</td>
                        <td>{new Date(f.failure_time).toLocaleDateString()}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}

export default MachineDetailPage;

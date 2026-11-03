import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  CheckCircle,
  AlertTriangle,
  XCircle,
  HelpCircle,
  RefreshCw,
  Radio,
  Database,
  ArrowRight,
  ShieldCheck,
  Cpu,
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
import { telemetryService, predictionService, evaluationService } from '../services';
import {
  Card,
  StatCard,
  Badge,
  LoadingSpinner,
  ErrorAlert,
  EmptyState,
} from '../components';

const QUALITY_COLORS = {
  normal: '#16a34a', // Emerald Green
  sensor_fault: '#f59e0b', // Amber
  invalid: '#dc2626', // Red
  missing: '#64748b', // Slate Gray
};

export function DataQualityPage() {
  const [qualityCounts, setQualityCounts] = useState(null);
  const [fleetAnomalies, setFleetAnomalies] = useState(null);
  const [recentFaults, setRecentFaults] = useState([]);
  const [edgeCasesData, setEdgeCasesData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchDataQuality = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      // Parallel execution of:
      // 1. Exact quality status counts from DB
      // 2. Machine-level sensor fault diagnostics
      // 3. Recent 10 sensor_fault telemetry events
      // 4. Edge cases verification audit
      const [counts, anomaliesRes, faultsRes, edgeRes] = await Promise.all([
        telemetryService.getDataQualityCounts(),
        predictionService.getFleetAnomalies({ page_size: 50 }),
        telemetryService.getHistoricalTelemetry({
          quality_status: 'sensor_fault',
          page_size: 10,
          page: 1,
        }),
        evaluationService.getEdgeCases().catch(() => null),
      ]);

      setQualityCounts(counts);
      setFleetAnomalies(anomaliesRes);
      setRecentFaults(faultsRes.items || []);
      setEdgeCasesData(edgeRes);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDataQuality();
  }, [fetchDataQuality]);

  if (loading && !qualityCounts) {
    return <LoadingSpinner message="Aggregating telemetry data quality across database..." />;
  }

  if (error && !qualityCounts) {
    return (
      <ErrorAlert
        title="Failed to Load Data Quality Metrics"
        message={error}
        onRetry={fetchDataQuality}
      />
    );
  }

  const {
    total = 0,
    normal = 0,
    sensor_fault = 0,
    invalid = 0,
    missing = 0,
    normalRate = 0,
    faultRate = 0,
    invalidRate = 0,
    missingRate = 0,
  } = qualityCounts || {};

  // Machines with sensor faults or low sensor reliability
  const faultyMachines =
    fleetAnomalies?.items?.filter(
      (m) => m.has_isolated_sensor_fault || m.sensor_reliability_index < 100
    ) || [];

  // Data quality pie distribution
  const qualityPieData = [
    { name: 'Normal', value: normal, color: QUALITY_COLORS.normal },
    { name: 'Sensor Fault', value: sensor_fault, color: QUALITY_COLORS.sensor_fault },
    { name: 'Invalid', value: invalid, color: QUALITY_COLORS.invalid },
    { name: 'Missing', value: missing, color: QUALITY_COLORS.missing },
  ].filter((d) => d.value > 0);

  // Bar chart representation
  const qualityBarData = [
    {
      status: 'Normal',
      count: normal,
      rate: Number(normalRate.toFixed(2)),
      fill: QUALITY_COLORS.normal,
    },
    {
      status: 'Sensor Fault',
      count: sensor_fault,
      rate: Number(faultRate.toFixed(2)),
      fill: QUALITY_COLORS.sensor_fault,
    },
    {
      status: 'Invalid',
      count: invalid,
      rate: Number(invalidRate.toFixed(2)),
      fill: QUALITY_COLORS.invalid,
    },
    {
      status: 'Missing',
      count: missing,
      rate: Number(missingRate.toFixed(2)),
      fill: QUALITY_COLORS.missing,
    },
  ];

  return (
    <div className="page-wrapper">
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Telemetry & Sensor Data Quality</h2>
          <p className="page-subheading">
            Instrumentation health, telemetry validity classifications, and machine-level sensor fault isolation.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-icon"
          onClick={fetchDataQuality}
          title="Refresh Data Quality"
        >
          <RefreshCw size={15} className={loading ? 'spin-animation' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* KPI Reading Counts */}
      <div className="stats-grid">
        <StatCard
          title="Total Telemetry Readings"
          value={total.toLocaleString()}
          subtitle="Processed time-series records"
          icon={Database}
          variant="default"
        />
        <StatCard
          title="Normal Readings"
          value={normal.toLocaleString()}
          subtitle={`${normalRate.toFixed(2)}% of total volume`}
          icon={CheckCircle}
          variant="normal"
        />
        <StatCard
          title="Sensor Fault Readings"
          value={sensor_fault.toLocaleString()}
          subtitle={`${faultRate.toFixed(2)}% instrumentation noise`}
          icon={AlertTriangle}
          variant="warning"
        />
        <StatCard
          title="Invalid Readings"
          value={invalid.toLocaleString()}
          subtitle={`${invalidRate.toFixed(2)}% out-of-range bounds`}
          icon={XCircle}
          variant="critical"
        />
        <StatCard
          title="Missing Readings"
          value={missing.toLocaleString()}
          subtitle={`${missingRate.toFixed(2)}% transmission dropouts`}
          icon={HelpCircle}
          variant="default"
        />
      </div>

      {/* Distribution Charts */}
      <div className="grid-2-col mt-4">
        <Card
          title="Telemetry Data Quality Distribution"
          subtitle="Proportion of verified readings vs degraded signals"
        >
          {qualityPieData.length > 0 ? (
            <div className="chart-container" style={{ height: 280 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={qualityPieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={65}
                    outerRadius={95}
                    paddingAngle={4}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} (${(percent * 100).toFixed(1)}%)`
                    }
                  >
                    {qualityPieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    formatter={(val, name) => [`${Number(val).toLocaleString()} readings`, name]}
                    contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1' }}
                  />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <EmptyState description="No telemetry data found." />
          )}
        </Card>

        <Card
          title="Quality Classification Breakdown"
          subtitle="Exact record counts per data quality classification"
        >
          <div className="chart-container" style={{ height: 280 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={qualityBarData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="status" stroke="#64748b" />
                <YAxis
                  stroke="#64748b"
                  tickFormatter={(val) =>
                    val >= 1000000
                      ? `${(val / 1000000).toFixed(1)}M`
                      : val >= 1000
                      ? `${(val / 1000).toFixed(0)}k`
                      : val
                  }
                />
                <Tooltip
                  formatter={(val, name, props) => [
                    `${Number(val).toLocaleString()} readings (${props.payload.rate}%)`,
                    'Count',
                  ]}
                  contentStyle={{ borderRadius: '6px', border: '1px solid #cbd5e1' }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {qualityBarData.map((entry, index) => (
                    <Cell key={`cell-bar-${index}`} fill={entry.fill} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Machine-Level Sensor Fault Information */}
      <Card
        title="Machine-Level Sensor Fault Diagnostics"
        subtitle="Machines currently exhibiting isolated sensor faults or instrumentation degradation"
        className="mt-4"
      >
        {faultyMachines.length === 0 ? (
          <EmptyState
            title="All Machine Sensors Healthy"
            description="No active isolated sensor faults detected across the monitored fleet."
            icon={ShieldCheck}
          />
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Machine Code</th>
                  <th>Machine Name</th>
                  <th>Type</th>
                  <th>Production Line</th>
                  <th>Sensor Reliability</th>
                  <th>Instrumentation Status</th>
                  <th>Fault Diagnosis Summary</th>
                  <th className="text-right">Action</th>
                </tr>
              </thead>
              <tbody>
                {faultyMachines.map((m) => (
                  <tr key={m.machine_id}>
                    <td>
                      <span className="font-semibold text-primary">{m.machine_code}</span>
                    </td>
                    <td>{m.machine_name}</td>
                    <td>{m.machine_type}</td>
                    <td>Line {m.line_id}</td>
                    <td>
                      <div className="health-bar-container">
                        <span className="health-bar-text">
                          {m.sensor_reliability_index.toFixed(0)}%
                        </span>
                        <div className="health-progress-bg">
                          <div
                            className={`health-progress-fill ${
                              m.sensor_reliability_index >= 90
                                ? 'bg-normal'
                                : m.sensor_reliability_index >= 70
                                ? 'bg-warning'
                                : 'bg-critical'
                            }`}
                            style={{
                              width: `${Math.max(5, m.sensor_reliability_index)}%`,
                            }}
                          />
                        </div>
                      </div>
                    </td>
                    <td>
                      {m.has_isolated_sensor_fault ? (
                        <span className="pill-badge pill-yellow">
                          Isolated Fault Isolated
                        </span>
                      ) : (
                        <span className="pill-badge pill-green">Nominal</span>
                      )}
                    </td>
                    <td>
                      <span className="text-sm text-secondary">
                        {m.explanation_summary || 'Sensor telemetry noise observed.'}
                      </span>
                    </td>
                    <td className="text-right">
                      <Link
                        to={`/machines/${m.machine_id}`}
                        className="btn btn-outline btn-xs"
                      >
                        Inspect
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Mandatory Edge Cases Verification Section */}
      <Card
        title="Mandatory Assignment Edge Cases Verification"
        subtitle="Verification of the 5 required edge-case scenarios with explicit issue_type and ground_truth labels"
        className="mt-4"
      >
        <div className="table-responsive">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>Scenario Name</th>
                <th>Issue Type</th>
                <th>Ground Truth Label</th>
                <th>Description</th>
                <th>Validation Guard Status</th>
              </tr>
            </thead>
            <tbody>
              {edgeCasesData?.cases?.map((ec) => (
                <tr key={ec.case_id}>
                  <td><strong>#{ec.case_id}</strong></td>
                  <td><span className="font-semibold text-slate-800">{ec.case_name}</span></td>
                  <td><code>{ec.issue_type}</code></td>
                  <td><Badge variant="neutral">{ec.ground_truth_label}</Badge></td>
                  <td className="text-sm text-secondary">{ec.scenario_description}</td>
                  <td>
                    {ec.detected ? (
                      <Badge variant="normal">Flagged & Handled</Badge>
                    ) : (
                      <Badge variant="critical">Undetected</Badge>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>

      {/* Recent Sensor Fault Event Records */}
      <Card
        title="Recent Sensor Fault Telemetry Stream"
        subtitle="Individual readings captured with sensor_fault quality classification"
        className="mt-4"
      >
        {recentFaults.length === 0 ? (
          <EmptyState
            title="No Recent Fault Events"
            description="No sensor_fault records returned in the query window."
          />
        ) : (
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Event ID</th>
                  <th>Sensor Code</th>
                  <th>Sensor Type</th>
                  <th>Observed Reading</th>
                  <th>Unit</th>
                  <th>Recorded Timestamp (UTC)</th>
                  <th>Quality Status</th>
                </tr>
              </thead>
              <tbody>
                {recentFaults.map((event) => (
                  <tr key={event.event_id}>
                    <td>
                      <span className="font-mono text-xs">#{event.event_id}</span>
                    </td>
                    <td>
                      <span className="font-semibold">{event.sensor_code}</span>
                    </td>
                    <td>{event.sensor_type}</td>
                    <td>
                      <span className="font-semibold text-warning">
                        {event.value !== null ? event.value.toFixed(2) : '--'}
                      </span>
                    </td>
                    <td>{event.unit || '--'}</td>
                    <td>
                      <span className="text-secondary text-sm">
                        {new Date(event.recorded_at).toLocaleString()}
                      </span>
                    </td>
                    <td>
                      <Badge variant="warning">{event.quality_status}</Badge>
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

export default DataQualityPage;

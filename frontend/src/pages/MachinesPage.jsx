import React, { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import {
  Search,
  Filter,
  RefreshCw,
  Cpu,
  ChevronRight,
  ShieldAlert,
  AlertCircle,
  CheckCircle,
  SlidersHorizontal,
} from 'lucide-react';
import { predictionService } from '../services';
import { PRODUCTION_LINES } from './OverviewPage';
import {
  Card,
  Badge,
  Pagination,
  LoadingSpinner,
  ErrorAlert,
  EmptyState,
} from '../components';

export function MachinesPage() {
  const [items, setItems] = useState([]);
  const [totalItems, setTotalItems] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedLine, setSelectedLine] = useState('');
  const [selectedRisk, setSelectedRisk] = useState('');
  const [anomaliesOnly, setAnomaliesOnly] = useState(false);

  const fetchMachines = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        page: currentPage,
        page_size: pageSize,
      };

      if (selectedLine) {
        params.line_id = Number(selectedLine);
      }
      if (selectedRisk) {
        params.risk_level = selectedRisk;
      }
      if (anomaliesOnly) {
        params.has_anomaly_only = true;
      }

      const response = await predictionService.getFleetAnomalies(params);
      setItems(response.items || []);
      setTotalItems(response.total || 0);
      setTotalPages(response.total_pages || 1);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, selectedLine, selectedRisk, anomaliesOnly]);

  useEffect(() => {
    fetchMachines();
  }, [fetchMachines]);

  // Client-side text filter on the page items
  const filteredItems = items.filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.machine_code.toLowerCase().includes(q) ||
      item.machine_name.toLowerCase().includes(q) ||
      item.machine_type.toLowerCase().includes(q) ||
      String(item.machine_id).includes(q)
    );
  });

  const handleFilterChange = () => {
    setCurrentPage(1);
  };

  return (
    <div className="page-wrapper">
      <div className="page-header-row">
        <div>
          <h2 className="page-heading">Equipment Fleet</h2>
          <p className="page-subheading">
            Live machine health indices, risk scores, and mechanical degradation classifications.
          </p>
        </div>
        <button
          type="button"
          className="btn btn-secondary btn-icon"
          onClick={fetchMachines}
          title="Refresh List"
        >
          <RefreshCw size={15} className={loading ? 'spin-animation' : ''} />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <Card className="filter-card">
        <div className="filters-grid">
          {/* Search Input */}
          <div className="search-input-wrapper">
            <Search size={16} className="search-icon" />
            <input
              type="text"
              className="form-input search-input"
              placeholder="Search by machine code, name, or type..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>

          {/* Line ID Filter */}
          <div className="filter-item">
            <select
              className="form-select"
              value={selectedLine}
              onChange={(e) => {
                setSelectedLine(e.target.value);
                handleFilterChange();
              }}
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

          {/* Risk Level Filter */}
          <div className="filter-item">
            <select
              className="form-select"
              value={selectedRisk}
              onChange={(e) => {
                setSelectedRisk(e.target.value);
                handleFilterChange();
              }}
              aria-label="Filter by Risk Level"
            >
              <option value="">All Risk Levels</option>
              <option value="Normal">Normal</option>
              <option value="Warning">Warning</option>
              <option value="Critical">Critical</option>
            </select>
          </div>

          {/* Toggle Anomalies Only */}
          <div className="filter-checkbox-wrapper">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={anomaliesOnly}
                onChange={(e) => {
                  setAnomaliesOnly(e.target.checked);
                  handleFilterChange();
                }}
              />
              <span>Anomalies Only</span>
            </label>
          </div>
        </div>
      </Card>

      {/* Main Table or States */}
      {loading && !items.length ? (
        <LoadingSpinner message="Querying machine fleet and calculating risk indexes..." />
      ) : error ? (
        <ErrorAlert
          title="Error Loading Machines"
          message={error}
          onRetry={fetchMachines}
        />
      ) : filteredItems.length === 0 ? (
        <Card>
          <EmptyState
            title="No Machines Found"
            description="No equipment matched the specified search and filter criteria."
            icon={Cpu}
          />
        </Card>
      ) : (
        <Card className="table-card">
          <div className="table-responsive">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Machine Code</th>
                  <th>Equipment Name</th>
                  <th>Category</th>
                  <th>Production Line</th>
                  <th>Health Index</th>
                  <th>Risk Score</th>
                  <th>Risk Level</th>
                  <th>Dominant Failure Mode</th>
                  <th>Sensor Reliability</th>
                  <th className="text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredItems.map((machine) => (
                  <tr key={machine.machine_id} className="hoverable-row">
                    <td>
                      <span className="font-semibold text-primary">
                        {machine.machine_code}
                      </span>
                    </td>
                    <td>
                      <div className="cell-title">{machine.machine_name}</div>
                    </td>
                    <td>
                      <span className="text-secondary">{machine.machine_type}</span>
                    </td>
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
                      <span className="font-semibold text-slate-800">
                        {machine.risk_score.toFixed(1)}
                      </span>
                    </td>
                    <td>
                      <Badge variant={machine.risk_level.toLowerCase()}>
                        {machine.risk_level}
                      </Badge>
                    </td>
                    <td>
                      {machine.dominant_failure_mode ? (
                        <span className="badge-tag">
                          {machine.dominant_failure_mode.replace('_', ' ')}
                        </span>
                      ) : (
                        <span className="text-muted">Nominal</span>
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
                        className="btn btn-primary btn-xs"
                      >
                        <span>Telemetry</span>
                        <ChevronRight size={14} />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="table-footer">
            <Pagination
              currentPage={currentPage}
              totalPages={totalPages}
              totalItems={totalItems}
              pageSize={pageSize}
              onPageChange={(page) => setCurrentPage(page)}
            />
          </div>
        </Card>
      )}
    </div>
  );
}

export default MachinesPage;

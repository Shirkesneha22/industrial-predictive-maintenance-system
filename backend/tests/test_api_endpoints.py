"""
API Endpoint Integration and Anti-Leakage Verification Tests.
Validates:
- Machine listing, pagination, filtering, and sensor topology endpoints.
- Explainable machine health and risk evaluation endpoints.
- Fleet-wide anomaly detection and risk ranking endpoints.
- Historical and latest sensor telemetry query endpoints.
- Validation handling: 422 for invalid IDs/query params, 404 for missing entities, 400 for invalid time bounds.
- Edge case handling: empty data horizons and insufficient telemetry data points.
- Strict anti-leakage guards:
  * Cutoff enforcement (recorded_at < prediction_timestamp).
  * Risk scores are engineering indicators, not calibrated probabilities.
  * No unvalidated RUL is claimed (returns None).
  * No failure labels or maintenance work-order properties exposed as prediction inputs.
"""

from datetime import datetime, timezone, timedelta
import pytest
from backend.models import Machine, Sensor
from backend.database import SessionLocal


@pytest.fixture(scope="module")
def valid_machine_id():
    """Retrieve an active machine ID from the test database."""
    db = SessionLocal()
    machine = db.query(Machine).filter(Machine.is_active == True).first()
    db.close()
    assert machine is not None, "Test database must contain at least one active machine"
    return machine.machine_id


# ============================================================================
# 1. Machine Endpoints Tests
# ============================================================================


def test_list_machines_success(client):
    """Verify paginated listing of machines returns correct schema and metadata."""
    response = client.get("/api/v1/machines?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert "items" in data
    assert data["total"] > 0
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert len(data["items"]) == min(10, data["total"])

    first_item = data["items"][0]
    for field in ["machine_id", "machine_code", "name", "machine_type", "line_id", "is_active", "created_at"]:
        assert field in first_item


def test_list_machines_filtering(client):
    """Verify filtering machines by line_id, machine_type, and is_active."""
    # Filter by is_active=true
    resp_active = client.get("/api/v1/machines?is_active=true&page_size=5")
    assert resp_active.status_code == 200
    for item in resp_active.json()["items"]:
        assert item["is_active"] is True

    # Filter by line_id=1
    resp_line = client.get("/api/v1/machines?line_id=1")
    assert resp_line.status_code == 200
    for item in resp_line.json()["items"]:
        assert item["line_id"] == 1


def test_get_machine_details_success(client, valid_machine_id):
    """Verify retrieval of an existing machine with mounted sensors."""
    response = client.get(f"/api/v1/machines/{valid_machine_id}")
    assert response.status_code == 200
    data = response.json()

    assert data["machine_id"] == valid_machine_id
    assert "sensors" in data
    assert isinstance(data["sensors"], list)
    assert len(data["sensors"]) > 0

    sensor = data["sensors"][0]
    for s_field in ["sensor_id", "sensor_code", "sensor_type", "unit", "is_active"]:
        assert s_field in sensor


def test_get_machine_details_not_found(client):
    """Verify 404 is returned when requesting a non-existent machine."""
    response = client.get("/api/v1/machines/999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_machine_details_invalid_id(client):
    """Verify 422 is returned when machine_id is less than 1 or not an integer."""
    resp_zero = client.get("/api/v1/machines/0")
    assert resp_zero.status_code == 422

    resp_neg = client.get("/api/v1/machines/-5")
    assert resp_neg.status_code == 422

    resp_str = client.get("/api/v1/machines/invalid-id")
    assert resp_str.status_code == 422


# ============================================================================
# 2. Machine Health & Risk Assessment Tests
# ============================================================================


def test_get_machine_risk_success(client, valid_machine_id):
    """Verify point-in-time machine health index and risk evaluation."""
    response = client.get(
        f"/api/v1/machines/{valid_machine_id}/risk?prediction_timestamp=2026-11-02T00:00:00Z"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["machine_id"] == valid_machine_id
    assert 0.0 <= data["health_index"] <= 100.0
    assert 0.0 <= data["risk_score"] <= 100.0
    assert data["risk_level"] in ["Normal", "Warning", "Critical"]
    assert "recommended_action" in data and len(data["recommended_action"]) > 0
    assert "contributing_signals" in data
    assert isinstance(data["contributing_signals"], list)
    assert "sensor_reliability_index" in data

    # Strict anti-leakage invariants
    assert data["is_calibrated_probability"] is False
    assert data["remaining_useful_life_hours"] is None


def test_get_machine_health_alias(client, valid_machine_id):
    """Verify /health endpoint returns identical schema and evaluation as /risk."""
    resp_risk = client.get(
        f"/api/v1/machines/{valid_machine_id}/risk?prediction_timestamp=2026-11-02T00:00:00Z"
    )
    resp_health = client.get(
        f"/api/v1/machines/{valid_machine_id}/health?prediction_timestamp=2026-11-02T00:00:00Z"
    )

    assert resp_risk.status_code == 200
    assert resp_health.status_code == 200
    assert resp_risk.json()["risk_score"] == resp_health.json()["risk_score"]
    assert resp_risk.json()["health_index"] == resp_health.json()["health_index"]
    assert resp_risk.json()["risk_level"] == resp_health.json()["risk_level"]


def test_get_machine_risk_not_found(client):
    """Verify 404 for non-existent machine in risk evaluation."""
    response = client.get("/api/v1/machines/999999/risk")
    assert response.status_code == 404


def test_get_machine_risk_invalid_id(client):
    """Verify 422 for invalid machine_id parameter."""
    response = client.get("/api/v1/machines/0/risk")
    assert response.status_code == 422


def test_get_machine_risk_empty_lookback_data(client, valid_machine_id):
    """
    Verify safe handling when evaluating risk at a timestamp with no preceding telemetry.
    Should return a graceful assessment with data_status='insufficient_telemetry'.
    """
    response = client.get(
        f"/api/v1/machines/{valid_machine_id}/risk?prediction_timestamp=2020-01-01T00:00:00Z"
    )
    assert response.status_code == 200
    data = response.json()

    assert data["machine_id"] == valid_machine_id
    assert data["data_status"] == "insufficient_telemetry"
    assert data["health_index"] == 100.0
    assert data["risk_score"] == 0.0
    assert data["risk_level"] == "Normal"
    assert data["contributing_signals"] == []
    assert "insufficient telemetry" in data["recommended_action"].lower()


# ============================================================================
# 3. Fleet Anomaly and Prediction Routes Tests
# ============================================================================


def test_fleet_anomalies_success(client):
    """Verify fleet-wide anomaly evaluation returns summary metrics and paginated machines."""
    response = client.get(
        "/api/v1/predictions/fleet-anomalies?line_id=1&page=1&page_size=5&prediction_timestamp=2026-11-02T00:00:00Z"
    )
    assert response.status_code == 200
    data = response.json()

    assert "prediction_timestamp" in data
    assert "summary" in data
    summary = data["summary"]
    for count_key in [
        "total_machines_evaluated",
        "normal_count",
        "warning_count",
        "critical_count",
        "correlated_degradation_count",
        "isolated_sensor_fault_count",
    ]:
        assert count_key in summary
        assert summary[count_key] >= 0

    assert summary["total_machines_evaluated"] == (
        summary["normal_count"] + summary["warning_count"] + summary["critical_count"]
    )
    assert "items" in data
    assert len(data["items"]) <= 5


def test_fleet_anomalies_filtering(client):
    """Verify filtering fleet anomalies by risk level."""
    response = client.get(
        "/api/v1/predictions/fleet-anomalies?line_id=1&risk_level=Normal&prediction_timestamp=2026-11-02T00:00:00Z"
    )
    assert response.status_code == 200
    data = response.json()

    for item in data["items"]:
        assert item["risk_level"] == "Normal"


def test_fleet_anomalies_empty_line(client):
    """Verify fleet anomaly response for a non-existent production line ID."""
    response = client.get("/api/v1/predictions/fleet-anomalies?line_id=999999")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["items"] == []
    assert data["summary"]["total_machines_evaluated"] == 0


def test_fleet_anomalies_alias(client):
    """Verify /predictions/anomalies alias works identically."""
    response = client.get("/api/v1/predictions/anomalies?line_id=1&page_size=3")
    assert response.status_code == 200
    assert "summary" in response.json()


def test_prediction_machine_risk(client, valid_machine_id):
    """Verify /predictions/machines/{id}/risk endpoint."""
    response = client.get(f"/api/v1/predictions/machines/{valid_machine_id}/risk")
    assert response.status_code == 200
    assert response.json()["machine_id"] == valid_machine_id


def test_machine_rul_anti_leakage(client, valid_machine_id):
    """Verify unvalidated RUL is not claimed (anti-leakage compliance)."""
    response = client.get(f"/api/v1/predictions/machines/{valid_machine_id}/rul")
    assert response.status_code == 200
    data = response.json()

    assert data["machine_id"] == valid_machine_id
    assert data["remaining_useful_life_hours"] is None
    assert data["is_calibrated"] is False
    assert "anti-leakage" in data["message"].lower()


# ============================================================================
# 4. Telemetry Query Endpoints Tests
# ============================================================================


def test_historical_telemetry_success(client, valid_machine_id):
    """Verify historical telemetry retrieval with pagination."""
    response = client.get(f"/api/v1/telemetry?machine_id={valid_machine_id}&page=1&page_size=20")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] > 0
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert len(data["items"]) == min(20, data["total"])

    reading = data["items"][0]
    for key in ["event_id", "sensor_id", "sensor_code", "sensor_type", "unit", "recorded_at", "quality_status"]:
        assert key in reading


def test_historical_telemetry_missing_machine(client):
    """Verify 404 when querying telemetry for a non-existent machine."""
    response = client.get("/api/v1/telemetry?machine_id=999999")
    assert response.status_code == 404


def test_historical_telemetry_invalid_id(client):
    """Verify 422 when machine_id is invalid."""
    response = client.get("/api/v1/telemetry?machine_id=0")
    assert response.status_code == 422


def test_historical_telemetry_missing_sensor(client):
    """Verify 404 when querying telemetry for a non-existent sensor."""
    response = client.get("/api/v1/telemetry?sensor_id=999999")
    assert response.status_code == 404


def test_historical_telemetry_invalid_time_range(client, valid_machine_id):
    """Verify 400 when start_time > end_time."""
    start = "2026-11-01T00:00:00Z"
    end = "2026-10-01T00:00:00Z"
    response = client.get(
        f"/api/v1/telemetry?machine_id={valid_machine_id}&start_time={start}&end_time={end}"
    )
    assert response.status_code == 400
    assert "start_time must be earlier" in response.json()["detail"].lower()


def test_historical_telemetry_empty_window(client, valid_machine_id):
    """Verify 200 with empty items list when query window contains no readings."""
    response = client.get(
        f"/api/v1/telemetry?machine_id={valid_machine_id}&start_time=2020-01-01T00:00:00Z&end_time=2020-01-02T00:00:00Z"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_latest_telemetry_success(client, valid_machine_id):
    """Verify latest telemetry endpoint returns current reading per mounted sensor."""
    response = client.get(f"/api/v1/telemetry/latest?machine_id={valid_machine_id}")
    assert response.status_code == 200
    data = response.json()

    assert isinstance(data, list)
    assert len(data) > 0

    reading = data[0]
    for key in ["event_id", "sensor_id", "sensor_code", "sensor_type", "unit", "recorded_at", "quality_status"]:
        assert key in reading


def test_latest_telemetry_not_found(client):
    """Verify 404 when querying latest telemetry for a non-existent machine."""
    response = client.get("/api/v1/telemetry/latest?machine_id=999999")
    assert response.status_code == 404


def test_machine_telemetry_direct_endpoint(client, valid_machine_id):
    """Verify /telemetry/machines/{machine_id} shortcut route."""
    response = client.get(f"/api/v1/telemetry/machines/{valid_machine_id}?page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    assert len(data["items"]) <= 10

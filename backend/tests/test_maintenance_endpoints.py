"""
Tests for Maintenance, Failures, and Evaluation Endpoints.
"""

import pytest


def test_maintenance_overview_endpoint(client):
    """Verify GET /api/v1/maintenance/overview returns aggregated statistics."""
    response = client.get("/api/v1/maintenance/overview")
    assert response.status_code == 200
    data = response.json()

    assert "total_work_orders" in data
    assert data["total_work_orders"] == 150
    assert "total_failures" in data
    assert data["total_failures"] == 150
    assert "total_downtime_minutes" in data
    assert data["total_downtime_minutes"] > 0
    assert "type_a_failures" in data
    assert "type_b_failures" in data
    assert data["total_spare_parts"] == 50
    assert data["total_technicians"] == 20


def test_maintenance_work_orders_endpoint(client):
    """Verify paginated listing of work orders."""
    response = client.get("/api/v1/maintenance/work-orders?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 150
    assert len(data["items"]) == 10
    item = data["items"][0]
    assert "work_order_id" in item
    assert "machine_id" in item
    assert "work_type" in item
    assert "status" in item


def test_maintenance_failures_endpoint(client):
    """Verify paginated listing of equipment failure events."""
    response = client.get("/api/v1/maintenance/failures?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 150
    assert len(data["items"]) == 10
    item = data["items"][0]
    assert "failure_id" in item
    assert "failure_type" in item
    assert "severity" in item
    assert "downtime_minutes" in item


from backend.database import SessionLocal
from backend.models import Machine


def test_machine_maintenance_history_endpoint(client):
    """Verify machine-specific maintenance history endpoint."""
    db = SessionLocal()
    machine = db.query(Machine).first()
    m_id = machine.machine_id
    db.close()

    response = client.get(f"/api/v1/machines/{m_id}/maintenance")
    assert response.status_code == 200
    data = response.json()

    assert data["machine_id"] == m_id
    assert "work_orders" in data
    assert "failures" in data


def test_evaluation_summary_endpoint(client):
    """Verify offline evaluation summary returns precision, recall, F1, and cohort breakdown."""
    response = client.get("/api/v1/evaluation/summary")
    assert response.status_code == 200
    data = response.json()

    assert "overall_metrics" in data
    metrics = data["overall_metrics"]
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert "true_positives" in metrics
    assert "false_negatives" in metrics

    assert "cohort_breakdown" in data
    assert "type_a_progressive" in data["cohort_breakdown"]
    assert "type_b_sudden" in data["cohort_breakdown"]
    assert data["cohort_breakdown"]["type_a_progressive"]["recall"] == 1.0


def test_evaluation_edge_cases_endpoint(client):
    """Verify evaluation edge-cases endpoint flags all 5 required edge cases."""
    response = client.get("/api/v1/evaluation/edge-cases")
    assert response.status_code == 200
    data = response.json()

    assert data["all_detected"] is True
    assert data["total_edge_cases"] == 5
    assert len(data["cases"]) == 5

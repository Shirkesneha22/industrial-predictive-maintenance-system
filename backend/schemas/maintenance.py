"""
Maintenance and Failure Event Schemas.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class MaintenanceWorkOrderResponse(BaseModel):
    """Schema for a single maintenance work order."""
    model_config = ConfigDict(from_attributes=True)

    work_order_id: int
    machine_id: int
    technician_id: Optional[int] = None
    work_type: str
    priority: str
    status: str
    description: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    technician_name: Optional[str] = None
    technician_code: Optional[str] = None
    machine_name: Optional[str] = None
    machine_code: Optional[str] = None
    parts_information: Optional[str] = None


class FailureEventResponse(BaseModel):
    """Schema for an equipment failure event."""
    model_config = ConfigDict(from_attributes=True)

    failure_id: int
    machine_id: int
    failure_type: str
    severity: str
    failure_time: datetime
    downtime_minutes: int
    description: Optional[str] = None
    created_at: datetime
    machine_name: Optional[str] = None
    machine_code: Optional[str] = None


class PaginatedWorkOrderResponse(BaseModel):
    """Paginated work orders response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[MaintenanceWorkOrderResponse]


class PaginatedFailureResponse(BaseModel):
    """Paginated failure events response."""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: List[FailureEventResponse]


class MaintenanceOverviewResponse(BaseModel):
    """Overall summary of maintenance and failure metrics."""
    total_work_orders: int
    completed_work_orders: int
    in_progress_work_orders: int
    pending_work_orders: int
    total_failures: int
    type_a_failures: int
    type_b_failures: int
    total_downtime_minutes: int
    total_downtime_hours: float
    total_spare_parts: int
    total_technicians: int

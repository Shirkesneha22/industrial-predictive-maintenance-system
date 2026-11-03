"""
API Routes Package.
Contains FastAPI API routers grouped by resource.
"""

from backend.routes.machines import router as machines_router
from backend.routes.predictions import router as predictions_router
from backend.routes.telemetry import router as telemetry_router
from backend.routes.maintenance import router as maintenance_router
from backend.routes.evaluation import router as evaluation_router

__all__ = [
    "machines_router",
    "predictions_router",
    "telemetry_router",
    "maintenance_router",
    "evaluation_router",
]

"""
Main entry point for the Industrial Predictive Maintenance FastAPI application.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

try:
    from backend.config import settings
    from backend.routes.machines import router as machines_router
    from backend.routes.predictions import router as predictions_router
    from backend.routes.telemetry import router as telemetry_router
    from backend.routes.maintenance import router as maintenance_router
    from backend.routes.evaluation import router as evaluation_router
except ImportError:
    from config import settings
    from routes.machines import router as machines_router
    from routes.predictions import router as predictions_router
    from routes.telemetry import router as telemetry_router
    from routes.maintenance import router as maintenance_router
    from routes.evaluation import router as evaluation_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Industrial Predictive Maintenance System API",
    version="0.1.0",
    docs_url="/docs",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
)

# Configure CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(
    machines_router,
    prefix=f"{settings.API_V1_PREFIX}/machines",
    tags=["Machines"],
)
app.include_router(
    predictions_router,
    prefix=f"{settings.API_V1_PREFIX}/predictions",
    tags=["Predictions"],
)
app.include_router(
    telemetry_router,
    prefix=f"{settings.API_V1_PREFIX}/telemetry",
    tags=["Telemetry"],
)
app.include_router(
    maintenance_router,
    prefix=f"{settings.API_V1_PREFIX}/maintenance",
    tags=["Maintenance"],
)
app.include_router(
    evaluation_router,
    prefix=f"{settings.API_V1_PREFIX}/evaluation",
    tags=["Evaluation"],
)


@app.get("/api/v1/docs", include_in_schema=False)
def api_v1_docs_redirect():
    """Redirect /api/v1/docs to the Swagger UI docs endpoint."""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
@app.get("/api/v1/health", tags=["System"], include_in_schema=False)
def health_check():
    """Health check endpoint to verify API availability."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "0.1.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app" if __package__ else "main:app", host="0.0.0.0", port=8000, reload=True)

# API Specification

The backend exposes RESTful endpoints with interactive Swagger documentation available at `/api/v1/docs`.

## Endpoint Route Groups

- **Health:**
  - `GET /health` - API server status.

- **Machines:**
  - `GET /api/v1/machines` - List all monitored machines.
  - `POST /api/v1/machines` - Register a new machine.
  - `GET /api/v1/machines/{id}` - Retrieve details and status of a specific machine.

- **Telemetry:**
  - `GET /api/v1/telemetry/latest` - Fetch the most recent sensor telemetry readings.
  - `POST /api/v1/telemetry` - Ingest batch sensor telemetry readings.

- **Predictions & Anomalies:**
  - `GET /api/v1/predictions/machines/{id}/rul` - Retrieve Remaining Useful Life (RUL) estimation.
  - `GET /api/v1/predictions/anomalies` - List active detected anomalies.

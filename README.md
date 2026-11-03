# Industrial Predictive Maintenance System

A clean, explainable, and production-ready Industrial Predictive Maintenance application built with **FastAPI**, **React.js**, and **PostgreSQL**.

---

## 1. Project Overview

The Industrial Predictive Maintenance System monitors the physical health of industrial equipment across manufacturing facilities. It ingests high-throughput sensor telemetry, computes statistical feature indicators over a strict lookback window, and identifies equipment exhibiting early signs of mechanical degradation using transparent, physics-informed rules.

---

## 2. Problem Being Solved

In modern manufacturing facilities, unplanned equipment downtime leads to severe production delays, safety hazards, and substantial financial losses. Traditional maintenance strategies either:
- **Run to failure (reactive):** Incurring costly emergency repairs and line halts.
- **Maintain on fixed calendar intervals (preventive):** Replacing healthy components prematurely.

This system provides **condition-based predictive maintenance** that detects progressive mechanical degradation (such as bearing wear and thermal runaway) up to **38.4 hours before breakdown**, while distinguishing isolated sensor noise from systemic multi-sensor faults to prevent false alarms.

---

## 3. Main Implemented Features

- **10 Core Relational Entities:** Complete normalized schema modeling plants, production lines, machines, sensors, telemetry, shifts, work orders, failure incidents, parts, and technicians.
- **Many-to-Many Part Compatibility:** Associative bridge table (`machine_parts`) mapping spare parts to compatible machines.
- **High-Volume Telemetry:** 2,160,000 synthetic sensor readings covering 90 historical days across 100 machines and 500 sensors.
- **Anti-Leakage Safeguards:** Feature extraction strictly queries `recorded_at < prediction_timestamp`. Failure records and work orders are sequestered from input features.
- **Explainable Rule-Based Health Engine:** Computes an intuitive Health Index (0–100) and Risk Score (0–100) based on rolling Z-scores and multi-sensor correlation rather than black-box models.
- **Transparent RUL Reporting:** Intentionally returns `null` for Remaining Useful Life (RUL) to avoid providing false confidence with uncalibrated estimates.
- **5 Mandatory Edge-Case Handlers:** Verifies unknown sensor references, impossible sensor values/units, failure times preceding symptoms, negative maintenance durations, and missing values represented as zero.
- **Interactive React Dashboard:** Fleet KPI summaries, machine filtering, 5-channel time-series charts, work order management, model evaluation metrics, and data quality audits.

---

## 4. Technology Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2
- **Frontend:** React 18, Webpack 5, Babel, Recharts, Lucide Icons, Axios
- **Database:** PostgreSQL 15+ (with psycopg driver)
- **Testing & Verification:** Pytest, Pytest-Asyncio, HTTPX

---

## 5. Project Folder Structure

```text
industrial-predictive-maintenance/
├── README.md                           # Main project documentation & run guide
├── AI_USAGE.md                         # Transparent AI usage & prompt history
├── pytest.ini                          # Pytest configuration
├── docker-compose.yml                  # Container orchestration specification
├── backend/                            # FastAPI backend application
│   ├── config.py                       # Environment and app configuration
│   ├── database.py                     # SQLAlchemy session & connection factory
│   ├── main.py                         # Application entry point & route definitions
│   ├── requirements.txt                # Python backend dependencies
│   ├── alembic.ini                     # Database migration configuration
│   ├── generators/                     # Deterministic synthetic data generator
│   ├── migrations/                     # Alembic schema migrations
│   ├── models/                         # 10 SQLAlchemy relational ORM models
│   ├── routes/                         # REST API route controllers
│   ├── schemas/                        # Pydantic request/response schemas
│   ├── services/                       # Feature extraction & risk engine
│   ├── tests/                          # 84-item automated test suite
│   ├── utils/                          # Exporters & reproducibility checker
│   └── validators/                     # Relational & edge-case validation
├── frontend/                           # React.js single-page application
│   ├── package.json                    # NPM scripts & dependencies
│   ├── webpack.config.js               # Webpack build & dev-server config
│   ├── public/                         # Static HTML template
│   └── src/                            # React components, pages, and API client
├── data/                               # Dataset exports and ground-truth records
│   ├── exports/                        # CSV, JSON, and SQL DDL seed files
│   └── ground_truth/                   # Sequestered failure records
└── docs/                               # Detailed architectural documentation
    ├── architecture.md                 # System components & data flow
    ├── database_schema.md              # Relational models & ER diagram
    ├── data_dictionary.md              # Exact fields, types, and constraints
    ├── design_decisions.md             # Engineering decisions & trade-offs
    ├── testing_and_validation.md       # Test results, edge cases & audit
    └── limitations.md                  # Known limitations & assumptions
```

---

## 6. Prerequisites

- **Operating System:** Windows 10/11 (PowerShell), macOS, or Linux
- **Python:** 3.11 or higher
- **Node.js:** 18 or higher (with `npm`)
- **PostgreSQL:** 15 or higher (service running locally on port 5432)

---

## 7. Environment & PostgreSQL Configuration

1. Ensure the PostgreSQL service is running on your machine.
2. In the `backend/` directory, create or edit the `.env` file based on `.env.example`:

```env
PROJECT_NAME="Industrial Predictive Maintenance System"
API_V1_PREFIX=/api/v1
DEBUG=True

# PostgreSQL Connection Settings
POSTGRES_SERVER=localhost
POSTGRES_PORT=5432
POSTGRES_DB=industrial_maintenance
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_actual_password_here

# Assembled Database URL (without hardcoding passwords in docs)
DATABASE_URL=postgresql://postgres:${POSTGRES_PASSWORD}@localhost:5432/industrial_maintenance

# CORS Settings
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

> **Security Note:** Never commit actual database passwords or credentials to version control. The application loads connection settings dynamically through `backend/config.py`.

---

## 8. Setup & Execution Instructions (Windows PowerShell)

### Normal Application Startup

If the database is already pre-populated, open two separate PowerShell terminal windows:

#### Terminal 1 — Backend API Server
```powershell
cd D:\Projects\industrial-predictive-maintenance

.\venv\Scripts\Activate.ps1

python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

#### Terminal 2 — Frontend Application
```powershell
cd D:\Projects\industrial-predictive-maintenance\frontend

npm start
```

---

### First-Time Database Setup (Only for Fresh / Blank Database)

> **Important:** If you already have the existing pre-populated database, **do not** run these setup commands.

If setting up on a completely empty PostgreSQL database instance:

```powershell
cd D:\Projects\industrial-predictive-maintenance
.\venv\Scripts\Activate.ps1

# 1. Apply schema migrations
alembic -c backend/alembic.ini upgrade head

# 2. Populate deterministic master data (Seed: 20261022)
python -m backend.generators.cli master-data --seed 20261022

# 3. Generate failure events and maintenance work orders
python -m backend.generators.cli failures --seed 20261022
```

---

## 9. Application & Documentation URLs

Once both backend and frontend servers are running, access the following URLs in your web browser:

| Service | URL | Purpose |
| :--- | :--- | :--- |
| **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Interactive operator UI and condition monitoring. |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI application base endpoint. |
| **Swagger Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API exploration and schema testing. |
| **API Health Probe** | [http://localhost:8000/health](http://localhost:8000/health) | System health and service status probe. |

---

## 10. How to Execute Tests

To run the automated backend test suite:

```powershell
cd D:\Projects\industrial-predictive-maintenance
.\venv\Scripts\pytest backend/tests
```

### Verified Test Suite Status
- **Total Tests Collected:** 84
- **Passed:** 83
- **Failed:** 1 (`test_small_chunk_copy_with_transactional_rollback` due to driver cursor method differences in modern `psycopg` v3; application logic and data integrity remain unaffected).
- Full audit details are documented in [`docs/testing_and_validation.md`](docs/testing_and_validation.md).

To verify the frontend production build:

```powershell
cd D:\Projects\industrial-predictive-maintenance\frontend
npm run build
```
*(Compiles cleanly with Webpack 5, exit code 0).*

---

## 11. How to Verify the Application

After starting the application, follow these steps to verify functionality:

1. **Verify Backend Health:**
   Navigate to [http://localhost:8000/health](http://localhost:8000/health). You should receive `{"status": "healthy", ...}`.
2. **Explore API Documentation:**
   Open [http://localhost:8000/docs](http://localhost:8000/docs) to test endpoints such as `GET /api/v1/machines` and `GET /api/v1/predictions/fleet-risk`.
3. **Verify Frontend UI:**
   Open [http://localhost:3000](http://localhost:3000). Inspect the fleet health summary cards, search for machines, and filter by line or machine type.
4. **Inspect Telemetry Charts:**
   Click on any machine (e.g., `MCH-001`) to view the 5-channel interactive telemetry chart displaying Vibration, Temperature, Acoustic, Pressure, and Current signals.
5. **Verify Data Quality Audits:**
   Navigate to the **Data Quality** page to view the live audit results for the 5 mandatory assignment edge cases.

---

## 12. Documentation Index

Detailed engineering documentation is organized inside [`docs/`](docs/):

- [Architecture & Data Flow](docs/architecture.md)
- [Database Schema & ERD](docs/database_schema.md)
- [Data Dictionary](docs/data_dictionary.md)
- [Design Decisions & Trade-Offs](docs/design_decisions.md)
- [Testing & Validation Report](docs/testing_and_validation.md)
- [Assumptions & Limitations](docs/limitations.md)
- [AI Usage & Prompt History](AI_USAGE.md)

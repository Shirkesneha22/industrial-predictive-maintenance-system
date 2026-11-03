# Industrial Predictive Maintenance System

A clean, explainable, and modular Industrial Predictive Maintenance application built with **FastAPI**, **React.js**, and **PostgreSQL**.

---

## 1. Project Overview

The Industrial Predictive Maintenance System monitors the physical health of industrial equipment across manufacturing facilities. It streams sensor telemetry, computes statistical feature indicators over a strict lookback window, and identifies equipment exhibiting early signs of mechanical degradation using transparent, physics-informed rules.

---

## 2. Problem Being Solved

In manufacturing facilities, unplanned equipment downtime leads to severe production delays, safety hazards, and financial losses. Traditional maintenance strategies either:
- **Run to failure (reactive):** Incurring costly emergency repairs and line halts.
- **Maintain on fixed calendar intervals (preventive):** Replacing healthy components prematurely.

This system provides **condition-based predictive maintenance**. In this synthetic dataset, progressive degradation drift is injected approximately 38.4 hours prior to labelled failure incidents, enabling rule-based evaluation to demonstrate early detection while distinguishing isolated sensor noise from systemic multi-sensor faults to prevent false alarms.

---

## 3. Main Implemented Features

- **10 Core Relational Entities:** Complete normalized schema modeling plants, production lines, machines, sensors, telemetry, shifts, work orders, failure incidents, parts, and technicians.
- **Many-to-Many Part Compatibility:** Associative bridge table (`machine_parts`) mapping spare parts to compatible machines.
- **Configurable Scale Telemetry:** 2,160,000 synthetic sensor readings (90 days, full scale) or 240,000 readings (10 days, starter scale) across 100 machines and 500 sensors.
- **Anti-Leakage Safeguards:** Feature extraction strictly queries `recorded_at < prediction_timestamp`. Failure records and work orders are sequestered from input features.
- **Explainable Rule-Based Health Engine:** Computes an intuitive Health Index (0–100) and Risk Score (0–100) based on rolling Z-scores and multi-sensor correlation rather than black-box models.
- **Transparent RUL Reporting:** Intentionally returns `null` for Remaining Useful Life (RUL) to avoid providing false confidence with uncalibrated estimates.
- **5 Mandatory Edge-Case Handlers:** Verifies unknown sensor references, impossible sensor values/units, failure times preceding symptoms, negative maintenance durations, and missing values represented as zero.
- **Interactive React Dashboard:** Fleet KPI summaries, machine filtering, 5-channel time-series charts, work order management, model evaluation metrics, and data quality audits.

---

## 4. Technology Stack

- **Backend:** Python 3.11+, FastAPI, Uvicorn, SQLAlchemy 2.0, Pydantic v2
- **Database Driver:** `psycopg` (v3 with binary C-extensions)
- **Frontend:** React 18, Webpack 5, Babel, Recharts, Lucide Icons, Axios
- **Database:** PostgreSQL 15+
- **Testing & Verification:** Pytest, Pytest-Asyncio, HTTPX

---

## 5. Project Folder Structure

```text
industrial-predictive-maintenance/
├── README.md                           # Main project documentation & run guide
├── Makefile                            # Orchestration targets (setup, test, validate, up, down)
├── docker-compose.yml                  # Container orchestration specification
├── scripts/
│   ├── setup.ps1                       # Windows PowerShell one-command setup
│   └── setup.sh                        # Linux/macOS Bash one-command setup
├── backend/                            # FastAPI backend application
│   ├── config.py                       # Environment and app configuration
│   ├── database.py                     # SQLAlchemy session & connection factory
│   ├── main.py                         # Application entry point & route definitions
│   ├── requirements.txt                # Python backend dependencies
│   ├── alembic.ini                     # Database migration configuration
│   ├── generators/                     # Deterministic synthetic data generators & CLI
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

- **Docker & Docker Compose** (Recommended path), OR:
- **Python:** 3.11 or higher
- **Node.js:** 18 or higher (with `npm`)
- **PostgreSQL:** 15 or higher (service running locally on port 5432)

---

## 7. Quick Start

### Option A: Docker Compose (Recommended)

To run the entire system in isolated Docker containers:

```bash
# 1. Start the PostgreSQL database and wait for healthcheck
docker compose up -d db

# 2. Run the one-command setup pipeline (migrations + seed + telemetry + export + validate)
docker compose run --rm setup

# 3. Start Backend API and Frontend Dashboard
docker compose up -d backend frontend
```

*Expected setup runtime: ~30-45 seconds in Docker.*

---

### Option B: Local Setup (Using Makefile or Automation Scripts)

#### 1. Configure Environment
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Ensure your local PostgreSQL credentials in `.env` match your database user and password.

#### 2. Run Setup Pipeline
Choose one of the following depending on your OS / tooling:

**Via Make (Linux, macOS, Windows with Make):**
```bash
# Fast starter dataset (~20 seconds):
make setup-starter

# Or full 90-day dataset (~2.5 minutes):
make setup
```

**Via PowerShell (Windows):**
```powershell
.\scripts\setup.ps1 -Scale starter
```

**Via Bash (macOS / Linux):**
```bash
./scripts/setup.sh starter
```

#### 3. Start Development Servers
In two separate terminal windows:

**Terminal 1 — Backend API:**
```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 — Frontend Application:**
```bash
npm --prefix frontend start
```

---

## 8. Expected Execution Runtime

| Pipeline Stage | Starter Scale (`--scale starter`) | Full Scale (`--scale full`) |
| :--- | :--- | :--- |
| **Schema Migration** | < 1 second | < 1 second |
| **Master Data Seed** | ~ 1 second | ~ 1 second |
| **Failure Events & Work Orders** | ~ 0.5 second | ~ 0.5 second |
| **Telemetry Ingestion** | ~ 15–20 seconds (240k rows) | ~ 2–3 minutes (2.16M rows) |
| **Data Export (CSV/JSON/SQL)** | ~ 2 seconds | ~ 12 seconds |
| **Data Validation** | ~ 2 seconds | ~ 3 seconds |
| **Total Runtime** | **~ 25–30 seconds** | **~ 2.5–3.5 minutes** |

---

## 9. Application & Documentation URLs

| Service | URL | Purpose |
| :--- | :--- | :--- |
| **Frontend Dashboard** | [http://localhost:3000](http://localhost:3000) | Interactive operator UI and condition monitoring. |
| **Backend API** | [http://localhost:8000](http://localhost:8000) | FastAPI application base endpoint. |
| **Swagger Interactive Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API exploration and schema testing. |
| **API Health Probe** | [http://localhost:8000/health](http://localhost:8000/health) | System health and service status probe. |

---

## 10. How to Run Automated Tests

The automated test suite runs via `pytest`:

```bash
pytest backend/tests
```

> **Database Requirement for Tests:**
> Tests require a running PostgreSQL instance accessible via the credentials configured in `.env` (or via `DATABASE_URL`). The default database targeted is `industrial_maintenance` (or overridden via `POSTGRES_DB=industrial_maintenance_test`).
> All database tests that stream or test synthetic telemetry utilize isolated transactions and execute strict rollback upon completion, preserving database state.

### Verified Test Suite Status
- **Collected Test Items:** 84
- **Passed:** 84 (100%)
- **Failed:** 0
- **Execution Time:** ~27 seconds

---

## 11. Individual CLI Stage Commands

Each generator stage can also be invoked independently via the unified CLI:

```bash
# Seed plants, lines, machines, sensors, parts, technicians
python -m backend.generators.cli master-data --seed 20261022

# Generate failure incidents and corrective work orders
python -m backend.generators.cli failures --seed 20261022

# Stream synthetic telemetry (starter or full)
python -m backend.generators.cli telemetry --seed 20261022 --scale starter

# Export tables to CSV, JSON, and SQL seed files
python -m backend.generators.cli export

# Run database integrity and edge-case validation
python -m backend.generators.cli validate

# Verify deterministic reproducibility and SHA-256 digests
python -m backend.generators.cli reproduce
```

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

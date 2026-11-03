# Database Design

## Overview

The system uses **PostgreSQL** to persist machine registries, sensor configurations, time-series telemetry streams, anomaly detections, and maintenance records.

## Core Entities

1. **`machines`**: Industrial assets (e.g., CNC milling machines, turbines, pumps, robotic arms).
2. **`sensors`**: Attached sensors per machine (vibration, thermal, pressure, rpm).
3. **`telemetry_records`**: Time-stamped sensor measurements (value, unit, quality flag).
4. **`predictions`**: Generated ML predictions (Remaining Useful Life (RUL), failure probability, health score).
5. **`maintenance_logs`**: Log of scheduled and reactive maintenance actions taken by engineers.

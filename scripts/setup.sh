#!/usr/bin/env bash
# ==============================================================================
# Industrial Predictive Maintenance - Automated Setup Pipeline (Bash)
# ==============================================================================

set -euo pipefail

SCALE="${1:-starter}"
PYTHON="${PYTHON:-}"

if [[ -z "$PYTHON" ]]; then
    if [[ -f "venv/bin/python" ]]; then
        PYTHON="venv/bin/python"
    elif [[ -f ".venv/bin/python" ]]; then
        PYTHON=".venv/bin/python"
    else
        PYTHON="python3"
    fi
fi

echo "============================================================"
echo " Industrial Predictive Maintenance - Setup Pipeline ($SCALE)"
echo " Using Python: $PYTHON"
echo "============================================================"

echo ""
echo "[1/5] Applying Database Migrations..."
"$PYTHON" -m alembic -c backend/alembic.ini upgrade head

echo ""
echo "[2/5] Seeding Deterministic Master Data..."
"$PYTHON" -m backend.generators.cli master-data

echo ""
echo "[3/5] Generating Failure Events & Work Orders..."
"$PYTHON" -m backend.generators.cli failures

echo ""
echo "[4/5] Streaming Telemetry Data (scale: $SCALE)..."
"$PYTHON" -m backend.generators.cli telemetry --scale "$SCALE"

echo ""
echo "[5/5] Exporting Data and Validating..."
"$PYTHON" -m backend.generators.cli export
"$PYTHON" -m backend.generators.cli validate

echo ""
echo "============================================================"
echo " Setup completed successfully! Ready to run application or tests."
echo "============================================================"

<#
.SYNOPSIS
    Automated setup script for Industrial Predictive Maintenance System (PowerShell).

.PARAMETER Scale
    Volume of dataset: 'starter' (10-day chunk) or 'full' (90-day complete dataset). Default is 'starter'.

.PARAMETER PythonPath
    Path to Python executable. Defaults to 'python' or active venv python.
#>
param (
    [ValidateSet("starter", "full")]
    [string]$Scale = "starter",

    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"

# Auto-detect virtualenv python if available
if (-not $PythonPath) {
    if (Test-Path "venv\Scripts\python.exe") {
        $PythonPath = "venv\Scripts\python.exe"
    } elseif (Test-Path ".venv\Scripts\python.exe") {
        $PythonPath = ".venv\Scripts\python.exe"
    } else {
        $PythonPath = "python"
    }
}

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Industrial Predictive Maintenance - Setup Pipeline ($Scale)" -ForegroundColor Cyan
Write-Host " Using Python: $PythonPath" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host "`n[1/5] Applying Database Migrations..." -ForegroundColor Yellow
& $PythonPath -m alembic -c backend/alembic.ini upgrade head

Write-Host "`n[2/5] Seeding Deterministic Master Data..." -ForegroundColor Yellow
& $PythonPath -m backend.generators.cli master-data

Write-Host "`n[3/5] Generating Failure Events & Work Orders..." -ForegroundColor Yellow
& $PythonPath -m backend.generators.cli failures

Write-Host "`n[4/5] Streaming Telemetry Data (scale: $Scale)..." -ForegroundColor Yellow
& $PythonPath -m backend.generators.cli telemetry --scale $Scale

Write-Host "`n[5/5] Exporting Data and Validating..." -ForegroundColor Yellow
& $PythonPath -m backend.generators.cli export
& $PythonPath -m backend.generators.cli validate

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host " Setup completed successfully! Ready to run application or tests." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

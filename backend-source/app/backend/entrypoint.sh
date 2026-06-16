#!/usr/bin/env bash
set -euo pipefail

# Run DB migration and apply validator before starting the app
echo "Running DB migration: migrate_customers_is_active.py"
python backend/scripts/migrate_customers_is_active.py || echo "Migration script exited non-zero"

echo "Applying customers validator"
python backend/scripts/create_customers_validator.py || echo "Validator script exited non-zero"

echo "Starting uvicorn"
exec "${@:-uvicorn backend.server:app --host 0.0.0.0 --port 8001}"

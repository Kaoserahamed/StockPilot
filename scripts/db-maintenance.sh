#!/bin/bash
# StockPilot Database Maintenance Script
# Usage: ./scripts/db-maintenance.sh
# Rebuilds indexes, updates statistics, and vacuums tables

set -euo pipefail

DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-stockpilot}"
DB_USER="${DB_USER:-stockpilot}"

echo "[maintenance] Starting database maintenance on ${DB_NAME}..."

# Reindex all tables
echo "[maintenance] Reindexing database..."
PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "REINDEX DATABASE $DB_NAME;" 2>/dev/null

# Update statistics
echo "[maintenance] Updating statistics..."
PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "ANALYZE;" 2>/dev/null

# Vacuum all tables
echo "[maintenance] Vacuuming..."
PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "VACUUM ANALYZE;" 2>/dev/null

# Show table sizes
echo "[maintenance] Table sizes:"
PGPASSWORD="${DB_PASSWORD:-changeme}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "
SELECT schemaname, tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables WHERE schemaname='public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
" 2>/dev/null

echo "[maintenance] Complete."


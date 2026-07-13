#!/bin/bash

# Load variables from .env
source .env

echo "=== Checking PostgreSQL Container ==="
docker ps | grep torgstat_postgres
if [ $? -ne 0 ]; then
  echo "[ERROR] Container is not running! Use: docker-compose up -d"
  exit 1
fi

echo "=== Checking Port ${POSTGRES_PORT} ==="
nc -zv localhost ${POSTGRES_PORT}
if [ $? -ne 0 ]; then
  echo "[ERROR] Postgres is not accessible on port ${POSTGRES_PORT}"
  exit 1
fi

echo "=== Verifying init script mounting ==="
# Check if the init script exists inside the container
docker exec -i torgstat_postgres ls /docker-entrypoint-initdb.d/init.sh > /dev/null 2>&1
if [ $? -ne 0 ]; then
  echo "[ERROR] init.sh not found inside the container! Check volume mounting in docker-compose.yml"
  exit 1
else
  echo "[OK] init.sh is mounted correctly."
fi

echo "=== Checking Database Connection ==="
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'
if [ $? -ne 0 ]; then
  echo "[ERROR] Failed to connect to the database!"
  exit 1
fi

echo "=== Checking Medallion Architecture Schemas ==="
# Verify raw, staging, and marts schemas exist
for schema in "$RAW_SCHEMA" "$STAGING_SCHEMA" "$MARTS_SCHEMA"; do
  docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name='$schema';" | grep -q "$schema"
  if [ $? -ne 0 ]; then
    echo "[ERROR] Schema '$schema' not found!"
    echo "--- DEBUG: Current schemas in database ---"
    docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c "\dn"
    echo "--- DEBUG: Recent PostgreSQL logs (potential init error) ---"
    docker logs torgstat_postgres --tail 20
    exit 1
  else
    echo "[OK] Schema '$schema' exists."
  fi
done

echo "=== Checking Database Users ==="
# Check ETL/dbt user
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT 1 FROM pg_roles WHERE rolname='$APP_DB_USER';" | grep -q 1
if [ $? -ne 0 ]; then
  echo "[ERROR] User '$APP_DB_USER' not found!"
  exit 1
else
  echo "[OK] User '$APP_DB_USER' exists."
fi

# Check Read-Only user
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT 1 FROM pg_roles WHERE rolname='$READONLY_USER';" | grep -q 1
if [ $? -ne 0 ]; then
  echo "[ERROR] User '$READONLY_USER' not found!"
  exit 1
else
  echo "[OK] User '$READONLY_USER' exists."
fi

echo "✅ All health checks passed successfully! DWH is ready."

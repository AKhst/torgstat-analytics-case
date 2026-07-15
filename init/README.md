# PostgreSQL Initialization

This directory contains `init.sh`, which is mounted into `/docker-entrypoint-initdb.d` by `docker-compose.yml`. The official PostgreSQL image executes this script during first-time database initialization.

## What the Script Creates

The script reads names and passwords from the container environment and performs the following actions:

1. Creates the schemas configured by `RAW_SCHEMA`, `STAGING_SCHEMA`, and `MARTS_SCHEMA`.
2. Creates the login role configured by `APP_DB_USER` if it does not exist.
3. Grants the application role database access and `USAGE, CREATE` on all three schemas.
4. Creates the login role configured by `READONLY_USER` if it does not exist.
5. Grants the read-only role database access and `USAGE` on the marts schema.

`POSTGRES_USER` owns the schemas. `APP_DB_USER` is intended for Python imports and dbt transformations. `READONLY_USER` is intended for BI access.

## Required Environment Variables

The following variables must be available inside the PostgreSQL container:

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB` | Database created by the PostgreSQL image |
| `POSTGRES_USER` | Administrative role and schema owner |
| `POSTGRES_PASSWORD` | Administrative role password |
| `RAW_SCHEMA` | Raw ingestion schema |
| `STAGING_SCHEMA` | Cleaned transformation schema |
| `MARTS_SCHEMA` | BI-ready schema |
| `APP_DB_USER` | Python/dbt login role |
| `APP_DB_PASSWORD` | Python/dbt role password |
| `READONLY_USER` | BI login role |
| `READONLY_PASSWORD` | BI role password |

Docker Compose reads these values from the root `.env` file and passes them to the container.

## First-Run Behavior

Start PostgreSQL from the repository root:

```bash
docker compose up -d
./check_postgres.sh
```

Initialization scripts run only when `/var/lib/postgresql/data` is empty. In this project that path is bind-mounted to `postgres_data/`. If the directory already contains a cluster, changing `init.sh` or `.env` and restarting the container will not rerun the script.

To initialize a fresh cluster without immediately deleting the old one:

```bash
docker compose down
mv postgres_data postgres_data.backup
docker compose up -d
```

After confirming the new database works, remove the backup manually if it is no longer needed. Choose a different backup name if `postgres_data.backup` already exists.

## Verify Initialization

List schemas:

```bash
docker exec -it torgstat_postgres \
  psql -U torgadmin -d torgdb -c "\dn"
```

List application roles:

```bash
docker exec -it torgstat_postgres \
  psql -U torgadmin -d torgdb \
  -c "SELECT rolname FROM pg_roles WHERE rolname IN ('appuser', 'readonly');"
```

Inspect initialization logs:

```bash
docker logs torgstat_postgres
```

Replace the example database and role names if your `.env` uses different values.

## Permission Caveat

`GRANT ... ON ALL TABLES` affects only tables that exist when the statement runs. During first-time initialization, the analytics tables do not exist yet. The current script also does not configure `ALTER DEFAULT PRIVILEGES`.

Tables created by `APP_DB_USER` are owned by that role, so the Python importer and dbt can use them. The dbt project grants `SELECT` on each marts relation through a post-hook. Tables created later outside dbt are not covered automatically; grant access to those with an administrative account:

```sql
GRANT USAGE ON SCHEMA marts TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA marts TO readonly;

ALTER DEFAULT PRIVILEGES FOR ROLE appuser IN SCHEMA marts
GRANT SELECT ON TABLES TO readonly;
```

The last statement applies to future tables created by `appuser` in `marts`.

## Common Failures

- **Empty schema or role names:** one or more required variables are missing from `.env`.
- **Script is mounted but not executed:** `postgres_data/` already contains an initialized cluster.
- **Role password did not change:** roles are created only when absent; the script does not alter existing passwords.
- **Permission denied for BI:** the table was created after initialization and no explicit or default grant was applied.
- **SQL syntax error near an identifier:** use simple unquoted PostgreSQL identifiers for configured database, schema, and role names.

-- Создание схемы
CREATE SCHEMA IF NOT EXISTS analytics AUTHORIZATION torgadmin;

-- Пользователь для приложения
CREATE USER appuser WITH PASSWORD 'app_secret_password';
GRANT CONNECT ON DATABASE torgdb TO appuser;
GRANT USAGE ON SCHEMA analytics TO appuser;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA analytics TO appuser;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO appuser;

-- Пользователь только для чтения (например для аналитиков или BI)
CREATE USER readonly WITH PASSWORD 'readonly_pass';
GRANT CONNECT ON DATABASE torgdb TO readonly;
GRANT USAGE ON SCHEMA analytics TO readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA analytics TO readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT SELECT ON TABLES TO readonly;

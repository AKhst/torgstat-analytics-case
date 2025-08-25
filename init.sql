-- Создание отдельной схемы для аналитики
CREATE SCHEMA IF NOT EXISTS analytics;

-- Установка прав
GRANT ALL PRIVILEGES ON SCHEMA analytics TO torguser;

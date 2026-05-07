#!/bin/bash

# Переменные из .env
source .env

echo "=== Проверка контейнера PostgreSQL ==="
docker ps | grep torgstat_postgres
if [ $? -ne 0 ]; then
  echo "Контейнер не запущен! Используй: docker compose up -d"
  exit 1
fi

echo "=== Проверка порта ${POSTGRES_PORT} ==="
nc -zv localhost ${POSTGRES_PORT}
if [ $? -ne 0 ]; then
  echo "Postgres не доступен на порту ${POSTGRES_PORT}"
  exit 1
fi

echo "=== Проверка подключения к базе ==="
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -c '\q'
if [ $? -ne 0 ]; then
  echo "Не удалось подключиться к базе!"
  exit 1
fi

echo "=== Проверка схемы analytics ==="
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT schema_name FROM information_schema.schemata WHERE schema_name='analytics';" | grep analytics
if [ $? -ne 0 ]; then
  echo "Схема analytics не найдена!"
  exit 1
fi

echo "=== Проверка пользователей appuser и readonly ==="
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT 1 FROM pg_roles WHERE rolname='appuser';" | grep 1
docker exec -i torgstat_postgres psql -U $POSTGRES_USER -d $POSTGRES_DB -tAc "SELECT 1 FROM pg_roles WHERE rolname='readonly';" | grep 1

echo "✅ Все проверки пройдены успешно!"

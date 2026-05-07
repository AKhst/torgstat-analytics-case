import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

# Единая точка входа для подключения к БД
from torgstat.db import get_engine

# Загружаем переменные из .env
load_dotenv()

# Получаем схему из окружения
SCHEMA = os.getenv("POSTGRES_SCHEMA", "analytics")

# Создаём движок SQLAlchemy через общий entrypoint
engine = get_engine()

# ----------------------
# Создаём схему, если её нет
# ----------------------
with engine.connect() as conn:
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
    print(f"[INFO] Схема {SCHEMA} создана или уже существует.")

# ----------------------
# Пути к CSV
# ----------------------
DATA_DIR = "/Users/admin/torgstat-analytics-case/data/"
files = ["plans.csv", "users.csv", "sessions.csv", "subscriptions.csv", "invoices.csv", "events.csv"]

# ----------------------
# Импорт данных в схему analytics
# ----------------------
for file in files:
    table_name = file.replace(".csv", "")  # Имя таблицы без расширения
    
    # Читаем CSV в DataFrame
    df = pd.read_csv(DATA_DIR+file)
    
    # Загружаем данные в PostgreSQL
    df.to_sql(table_name, engine, schema=SCHEMA, if_exists='replace', index=False)
    print(f"[INFO] Данные из {file} загружены в таблицу {SCHEMA}.{table_name}.")
# ----------------------
# Проверка
# ----------------------
with engine.connect() as conn:
    result = conn.exec_driver_sql(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{SCHEMA}';")
    tables = result.fetchall()
    print(f"[INFO] Таблицы в схеме {SCHEMA}: {[row[0] for row in tables]}")
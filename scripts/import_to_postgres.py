import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настраиваем подключение с использованием пользователя ETL (appuser)
DB_USER = os.getenv("APP_DB_USER", "appuser")
DB_PASS = os.getenv("APP_DB_PASSWORD", "app_secret_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5433")
DB_NAME = os.getenv("POSTGRES_DB", "torgdb")

# Загружаем данные строго в слой raw
SCHEMA = os.getenv("RAW_SCHEMA", "raw")

DB_URI = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

files = [
    "plans.csv",
    "users.csv",
    "sessions.csv",
    "subscriptions.csv",
    "invoices.csv",
    "events.csv",
]


def load_data():
    print(f"[INFO] Connecting to database: {DB_HOST}:{DB_PORT}/{DB_NAME} as {DB_USER}")

    # Создаем движок SQLAlchemy
    engine = create_engine(DB_URI)

    # Используем begin() для автоматического коммита транзакции
    with engine.begin() as conn:
        # Убедимся, что схема существует
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
        print(f"[INFO] Schema '{SCHEMA}' is ready.")

        # Читаем каждый CSV файл и загружаем его
        for file in files:
            table_name = file.replace(".csv", "")
            file_path = os.path.join(DATA_DIR, file)

            if not os.path.exists(file_path):
                print(f"[WARNING] File {file} not found. Skipping {table_name} table.")
                continue

            df = pd.read_csv(file_path)

            # Удаляем старую таблицу (вместе с dbt views, если они уже были созданы поверх)
            conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.{table_name} CASCADE;"))

            # Загружаем DataFrame в Postgres
            print(f"[INFO] Loading {len(df)} rows into {SCHEMA}.{table_name}...")
            df.to_sql(
                name=table_name,
                con=conn,
                schema=SCHEMA,
                if_exists="replace",
                index=False,
                method="multi",
                chunksize=5000,
            )
            print(f"  ✅ Success: {table_name}")

    print("[SUCCESS] All raw data has been imported to the DWH.")


if __name__ == "__main__":
    load_data()
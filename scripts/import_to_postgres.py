import os
import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv

# Единая точка входа для подключения к БД
from torgstat.db import get_engine

load_dotenv()
SCHEMA = os.getenv("POSTGRES_SCHEMA", "analytics")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

files = [
    "plans.csv", "users.csv", "sessions.csv", 
    "subscriptions.csv", "invoices.csv", "events.csv"
]

def load_data():
    engine = get_engine()

    # Используем begin() для автоматического коммита транзакции
    with engine.begin() as conn:
        # 1. Создаем схему
        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};"))
        print(f"[INFO] Схема {SCHEMA} готова.")

        # 2. Загружаем файлы
        for file in files:
            table_name = file.replace(".csv", "")
            file_path = os.path.join(DATA_DIR, file)
            
            if not os.path.exists(file_path):
                print(f"[WARNING] Файл {file} не найден. Пропускаем.")
                continue
            
            df = pd.read_csv(file_path)
            
            # Принудительно удаляем старую таблицу и все зависящие от нее dbt-вьюхи
            conn.execute(text(f"DROP TABLE IF EXISTS {SCHEMA}.{table_name} CASCADE;"))
            
            # Теперь Pandas может спокойно создать новую таблицу
            df.to_sql(
                name=table_name, 
                con=conn, 
                schema=SCHEMA, 
                if_exists='replace', 
                index=False,
                method='multi',
                chunksize=5000
            )
            print(f"[INFO] Загружено {len(df)} строк из {file} в таблицу {SCHEMA}.{table_name}.")

if __name__ == "__main__":
    load_data()
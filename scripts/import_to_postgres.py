import logging
import os
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import BigInteger, DateTime, Text, create_engine, text
from sqlalchemy.engine import URL

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

DB_USER = os.getenv("APP_DB_USER", "appuser")
DB_PASSWORD = os.getenv("APP_DB_PASSWORD", "app_secret_password")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = int(os.getenv("POSTGRES_PORT", "5433"))
DB_NAME = os.getenv("POSTGRES_DB", "torgdb")
SCHEMA = os.getenv("RAW_SCHEMA", "raw")

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

FILE_SCHEMAS = {
    "workspaces.csv": [
        "workspace_id",
        "workspace_name",
        "created_at",
        "country_code",
        "customer_segment",
        "billing_currency",
        "is_active",
    ],
    "plans.csv": [
        "plan_id",
        "plan_name",
        "tier_rank",
        "monthly_price",
        "annual_price",
        "is_active",
    ],
    "users.csv": [
        "user_id",
        "workspace_id",
        "created_at",
        "country_code",
        "user_role",
        "signup_type",
        "has_gdpr_consent",
        "is_active",
        "deleted_at",
    ],
    "sessions.csv": [
        "session_id",
        "user_id",
        "started_at",
        "utm_source",
        "utm_medium",
        "is_first_session",
    ],
    "subscriptions.csv": [
        "subscription_id",
        "workspace_id",
        "started_at",
        "ended_at",
        "status",
    ],
    "subscription_plan_history.csv": [
        "subscription_plan_period_id",
        "subscription_id",
        "plan_id",
        "billing_frequency",
        "valid_from",
        "valid_to",
        "change_type",
    ],
    "invoices.csv": [
        "invoice_id",
        "subscription_id",
        "workspace_id",
        "plan_id",
        "billing_frequency",
        "issued_at",
        "due_at",
        "period_start",
        "period_end",
        "currency",
        "net_amount",
        "tax_amount",
        "gross_amount",
        "payment_status",
        "paid_at",
    ],
    "events.csv": ["workspace_id", "event_date", "event_name", "properties"],
    "fx_rates.csv": ["rate_date", "base_currency", "quote_currency", "rate"],
}

IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def validate_identifier(value: str, variable_name: str) -> None:
    if not IDENTIFIER_PATTERN.fullmatch(value):
        raise ValueError(f"{variable_name} must be a valid unquoted PostgreSQL identifier")


def read_source_file(file_name: str) -> pd.DataFrame:
    file_path = DATA_DIR / file_name
    dataframe = pd.read_csv(file_path)
    expected_columns = FILE_SCHEMAS[file_name]

    if dataframe.columns.tolist() != expected_columns:
        raise ValueError(
            f"Unexpected columns in {file_name}. "
            f"Expected {expected_columns}, received {dataframe.columns.tolist()}"
        )

    if dataframe.empty:
        raise ValueError(f"Source file {file_name} is empty")

    return dataframe


def add_load_metadata(
    dataframe: pd.DataFrame,
    file_name: str,
    load_batch_id: str,
    loaded_at_utc: datetime,
) -> pd.DataFrame:
    result = dataframe.copy()
    result["_source_file"] = file_name
    result["_source_row_number"] = range(1, len(result) + 1)
    result["_load_batch_id"] = load_batch_id
    result["_loaded_at_utc"] = loaded_at_utc
    return result


def load_data() -> None:
    validate_identifier(SCHEMA, "RAW_SCHEMA")

    missing_files = [name for name in FILE_SCHEMAS if not (DATA_DIR / name).is_file()]
    if missing_files:
        raise FileNotFoundError(f"Required source files are missing: {', '.join(missing_files)}")

    load_batch_id = str(uuid.uuid4())
    loaded_at_utc = datetime.now(timezone.utc)
    source_dataframes = {
        file_name: add_load_metadata(
            read_source_file(file_name),
            file_name,
            load_batch_id,
            loaded_at_utc,
        )
        for file_name in FILE_SCHEMAS
    }

    connection_url = URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
    )
    engine = create_engine(connection_url, pool_pre_ping=True)

    logger.info(
        "Loading batch %s into %s:%s/%s.%s as %s",
        load_batch_id,
        DB_HOST,
        DB_PORT,
        DB_NAME,
        SCHEMA,
        DB_USER,
    )

    metadata_types = {
        "_source_file": Text(),
        "_source_row_number": BigInteger(),
        "_load_batch_id": Text(),
        "_loaded_at_utc": DateTime(timezone=True),
    }

    try:
        with engine.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{SCHEMA}"'))

            for file_name, dataframe in source_dataframes.items():
                table_name = Path(file_name).stem
                connection.execute(
                    text(f'DROP TABLE IF EXISTS "{SCHEMA}"."{table_name}" CASCADE')
                )
                dataframe.to_sql(
                    name=table_name,
                    con=connection,
                    schema=SCHEMA,
                    if_exists="fail",
                    index=False,
                    method="multi",
                    chunksize=5000,
                    dtype=metadata_types,
                )
                logger.info("Loaded %s rows into %s.%s", len(dataframe), SCHEMA, table_name)
    finally:
        engine.dispose()

    logger.info("Raw batch %s loaded successfully", load_batch_id)


if __name__ == "__main__":
    load_data()

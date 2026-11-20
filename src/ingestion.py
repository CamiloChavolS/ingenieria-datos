"""Atomically full-refresh the PostgreSQL Bronze source tables from CSV."""

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine, inspect, text


SCRIPT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(SCRIPT_DIR, "..")))
DATA_DIR = Path(os.path.abspath(os.path.join(PROJECT_ROOT, "data")))
load_dotenv(os.path.abspath(os.path.join(PROJECT_ROOT, ".env")))

FILES_TO_TABLES = {
    "ravenstack_accounts.csv": "accounts",
    "ravenstack_subscriptions.csv": "subscriptions",
    "ravenstack_feature_usage.csv": "feature_usage",
    "ravenstack_support_tickets.csv": "support_tickets",
    "ravenstack_churn_events.csv": "churn_events",
}


def main() -> None:
    """Validate all inputs, then replace the full Bronze snapshot atomically."""
    source_paths = {
        table_name: DATA_DIR / file_name
        for file_name, table_name in FILES_TO_TABLES.items()
    }
    missing_files = [path for path in source_paths.values() if not path.is_file()]
    if missing_files:
        missing_list = ", ".join(str(path) for path in missing_files)
        raise FileNotFoundError(f"Faltan archivos CSV de origen: {missing_list}")

    # Read every source before opening the transaction so malformed CSVs cannot
    # leave a partially refreshed set of Bronze tables.
    source_data = {
        table_name: pd.read_csv(source_path)
        for table_name, source_path in source_paths.items()
    }

    database_url = URL.create(
        drivername=os.getenv("DB_DRIVER", "postgresql+psycopg2"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "ravenstack_db"),
    )
    engine = create_engine(database_url, pool_pre_ping=True)

    try:
        with engine.begin() as connection:
            connection.execute(text("CREATE SCHEMA IF NOT EXISTS bronze"))
            existing_tables = set(inspect(connection).get_table_names(schema="bronze"))
            for table_name, data in source_data.items():
                if table_name in existing_tables:
                    connection.execute(
                        text(f'DELETE FROM bronze."{table_name}"')
                    )
                data.to_sql(
                    name=table_name,
                    con=connection,
                    schema="bronze",
                    if_exists="append",
                    index=False,
                )
    finally:
        engine.dispose()

    for table_name, data in source_data.items():
        print(f"Cargada bronze.{table_name}: {len(data)} filas")
    print("Full refresh de Bronze completado; se cargó un snapshot consistente.")


if __name__ == "__main__":
    main()

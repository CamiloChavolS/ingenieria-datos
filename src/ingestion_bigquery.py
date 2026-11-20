"""Load the raw CSV files into BigQuery Bronze using ADC authentication."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.api_core.exceptions import NotFound
from google.cloud import bigquery


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


def main():
    project_id = os.getenv("GCP_PROJECT_ID")
    location = os.getenv("BQ_LOCATION", "US")
    if not project_id:
        raise ValueError("Define GCP_PROJECT_ID en .env antes de cargar BigQuery.")

    source_files = {
        table_name: Path(os.path.abspath(os.path.join(DATA_DIR, filename)))
        for filename, table_name in FILES_TO_TABLES.items()
    }
    missing = [str(path) for path in source_files.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Faltan CSV de origen: " + ", ".join(missing))

    client = bigquery.Client(project=project_id)
    dataset_id = f"{project_id}.bronze"
    try:
        client.get_dataset(dataset_id)
    except NotFound as exc:
        raise RuntimeError(
            "El dataset Bronze debe aprovisionarse con Terraform antes de la ingesta."
        ) from exc

    for table_name, csv_path in source_files.items():
        table_id = f"{project_id}.bronze.{table_name}"
        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            autodetect=True,
            write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        )
        with csv_path.open("rb") as csv_file:
            job = client.load_table_from_file(
                csv_file,
                table_id,
                job_config=job_config,
                location=location,
            )
        job.result()
        loaded = client.get_table(table_id)
        print(f"Cargada bronze.{table_name}: {loaded.num_rows} filas")

    print(f"Ingesta completa en BigQuery: proyecto={project_id}, ubicación={location}")


if __name__ == "__main__":
    main()

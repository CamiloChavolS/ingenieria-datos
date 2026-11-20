"""Train and save the RavenStack churn prediction model."""

import os
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split


SCRIPT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")))
load_dotenv(os.path.abspath(os.path.join(PROJECT_ROOT, ".env")))
MODELS_DIR = Path(os.path.abspath(os.path.join(PROJECT_ROOT, "models_saved")))
MODEL_PATH = Path(os.path.abspath(os.path.join(MODELS_DIR, "churn_model.joblib")))
NUMERIC_FEATURES = [
    "monthly_recurring_revenue",
    "total_feature_usage",
    "total_usage_errors",
    "total_support_tickets",
    "avg_resolution_time_hours",
    "avg_satisfaction_score",
]


def database_url():
    """Build the PostgreSQL URL from environment variables."""
    return URL.create(
        drivername=os.getenv("DB_DRIVER", "postgresql+psycopg2"),
        username=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        database=os.getenv("DB_NAME", "ravenstack_db"),
    )


def main():
    query = """
        SELECT plan_tier, monthly_recurring_revenue,
               total_feature_usage, total_usage_errors, total_support_tickets,
               avg_resolution_time_hours, avg_satisfaction_score, is_churned
        FROM gold.mart_customer_churn
        WHERE is_churned IS NOT NULL
    """
    backend = os.getenv("ML_BACKEND", "postgres").lower()
    if backend == "bigquery":
        try:
            from google.cloud import bigquery
        except ImportError as exc:
            raise RuntimeError(
                "Instala google-cloud-bigquery para entrenar desde BigQuery."
            ) from exc
        project_id = os.getenv("GCP_PROJECT_ID")
        if not project_id:
            raise ValueError("Define GCP_PROJECT_ID para entrenar desde BigQuery.")
        print("Cargando datos desde BigQuery...")
        query = query.replace(
            "FROM gold.mart_customer_churn",
            f"FROM `{project_id}.gold.mart_customer_churn`",
        )
        client = bigquery.Client(project=project_id)
        data = pd.DataFrame(
            [dict(row.items()) for row in client.query(query).result()]
        )
    elif backend == "postgres":
        print("Cargando datos desde PostgreSQL...")
        engine = create_engine(database_url(), pool_pre_ping=True)
        with engine.connect() as connection:
            data = pd.read_sql_query(query, con=connection)
        engine.dispose()
    else:
        raise ValueError("ML_BACKEND debe ser 'postgres' o 'bigquery'.")

    if data.empty or data["is_churned"].nunique() < 2:
        raise ValueError("Se requieren datos de ambas clases para entrenar el modelo.")

    data["plan_tier"] = data["plan_tier"].fillna("Unknown")
    for column in NUMERIC_FEATURES:
        data[column] = pd.to_numeric(data[column], errors="coerce")
        data[column] = data[column].fillna(data[column].median()).fillna(0)

    model_data = pd.get_dummies(data, columns=["plan_tier"], drop_first=True)
    features = model_data.drop(columns=["is_churned"])
    target = model_data["is_churned"].astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    print("Entrenando RandomForest...")
    model = RandomForestClassifier(
        n_estimators=300,
        class_weight="balanced",
        min_samples_leaf=5,
        random_state=42,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    print("\n--- Resultados del modelo ---")
    report = classification_report(
        y_test,
        predictions,
        zero_division=0,
        output_dict=True,
    )
    print(classification_report(y_test, predictions, zero_division=0))
    holdout_roc_auc = roc_auc_score(y_test, probabilities)
    model.holdout_roc_auc_ = float(holdout_roc_auc)
    model.holdout_accuracy_ = float(report["accuracy"])
    model.holdout_churn_precision_ = float(report["1"]["precision"])
    model.holdout_churn_recall_ = float(report["1"]["recall"])
    print(f"ROC-AUC: {holdout_roc_auc:.4f}")

    os.makedirs(os.path.abspath(MODELS_DIR), exist_ok=True)
    joblib.dump(model, os.path.abspath(MODEL_PATH))
    print(f"Modelo guardado en: {os.path.abspath(MODEL_PATH)}")


if __name__ == "__main__":
    main()

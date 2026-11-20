"""Export privacy-minimized aggregates for the GitHub Pages portfolio demo."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine


SCRIPT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(SCRIPT_DIR, "..")))
DATA_DIR = Path(os.path.abspath(os.path.join(PROJECT_ROOT, "docs", "assets")))
MODEL_PATH = Path(os.path.abspath(
    os.path.join(PROJECT_ROOT, "models_saved", "churn_model.joblib")
))
OUTPUT_PATH = Path(os.path.abspath(os.path.join(DATA_DIR, "demo_data.json")))

load_dotenv(os.path.abspath(os.path.join(PROJECT_ROOT, ".env")))


def database_url():
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
        SELECT industry, country, plan_tier,
               monthly_recurring_revenue, is_churned, is_active
        FROM gold.mart_customer_churn
    """
    engine = create_engine(database_url(), pool_pre_ping=True)
    try:
        with engine.connect() as connection:
            data = pd.read_sql_query(query, con=connection)
    finally:
        engine.dispose()

    if data.empty:
        raise ValueError("gold.mart_customer_churn no contiene filas.")
    if not MODEL_PATH.is_file():
        raise FileNotFoundError(f"No se encontró el modelo local: {MODEL_PATH}")

    for column in ("industry", "country", "plan_tier"):
        data[column] = data[column].fillna("Unknown").astype(str)
    for column in ("monthly_recurring_revenue", "is_churned", "is_active"):
        data[column] = pd.to_numeric(data[column], errors="coerce").fillna(0)

    data["mrr_band"] = pd.cut(
        data["monthly_recurring_revenue"],
        bins=[float("-inf"), 500, 2_000, 10_000, float("inf")],
        labels=["< $500", "$500–$1.999", "$2.000–$9.999", "$10.000+"],
        right=False,
    ).astype(str)
    data["active_mrr"] = data["monthly_recurring_revenue"].where(
        data["is_active"].eq(1), 0
    )

    grouped = (
        data.groupby(
            ["industry", "country", "plan_tier", "mrr_band"],
            dropna=False,
            observed=True,
        )
        .agg(
            customers=("is_churned", "size"),
            churned=("is_churned", "sum"),
            active=("is_active", "sum"),
            active_mrr=("active_mrr", "sum"),
        )
        .reset_index()
        .sort_values(["industry", "country", "plan_tier", "mrr_band"])
    )

    churned = int(data["is_churned"].sum())
    active = int(data["is_active"].sum())
    model = joblib.load(MODEL_PATH)
    model_metrics = {
        "accuracy": float(model.holdout_accuracy_),
        "churn_precision": float(model.holdout_churn_precision_),
        "churn_recall": float(model.holdout_churn_recall_),
        "roc_auc": float(model.holdout_roc_auc_),
    }
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": "Synthetic SaaS Subscription & Churn dataset by Rivalytics",
        "privacy_note": (
            "Aggregated counts only; account IDs, company names and comments "
            "are not included."
        ),
        "kpis": {
            "customers": int(len(data)),
            "active": active,
            "churned": churned,
            "churn_rate_pct": round(churned / len(data) * 100, 2),
            "active_mrr": round(float(data["active_mrr"].sum()), 2),
        },
        "model_metrics": model_metrics,
        "segments": [
            {
                **row,
                "customers": int(row["customers"]),
                "churned": int(row["churned"]),
                "active": int(row["active"]),
                "active_mrr": round(float(row["active_mrr"]), 2),
            }
            for row in grouped.to_dict(orient="records")
        ],
    }

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(
        f"Snapshot estático generado: {OUTPUT_PATH} "
        f"({len(payload['segments'])} agregaciones; sin identificadores)."
    )


if __name__ == "__main__":
    main()

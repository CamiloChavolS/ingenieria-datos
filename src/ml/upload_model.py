"""Upload the trained model to a private GCS bucket for deployment."""

import os
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage


SCRIPT_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
PROJECT_ROOT = Path(os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..")))
load_dotenv(os.path.abspath(os.path.join(PROJECT_ROOT, ".env")))


def main():
    bucket_name = os.environ["MODEL_BUCKET"]
    commit_sha = os.environ.get("CI_COMMIT_SHA", "local")
    job_id = os.environ.get("CI_JOB_ID", "local")
    model_path = Path(
        os.path.abspath(
            os.path.join(PROJECT_ROOT, "models_saved", "churn_model.joblib")
        )
    )
    if not model_path.is_file():
        raise FileNotFoundError(f"No existe el modelo entrenado: {model_path}")
    destination = f"models/churn_model-{commit_sha}-{job_id}.joblib"
    storage.Client().bucket(bucket_name).blob(destination).upload_from_filename(
        str(model_path), content_type="application/octet-stream"
    )
    model_uri = f"gs://{bucket_name}/{destination}"
    pipeline_dir = os.getenv("CI_PROJECT_DIR")
    if pipeline_dir and os.getenv("CI_JOB_ID"):
        dotenv_path = Path(os.path.abspath(os.path.join(pipeline_dir, "model.env")))
        dotenv_path.write_text(f"MODEL_GCS_URI={model_uri}\n", encoding="utf-8")
    print(f"Modelo cargado a {model_uri}")


if __name__ == "__main__":
    main()

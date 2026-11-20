"""Create short-lived Google ADC configuration from GitLab OIDC variables."""

import json
import os
from pathlib import Path


def main():
    project_number = os.environ["GCP_PROJECT_NUMBER"]
    pool_id = os.environ["GCP_WIF_POOL"]
    provider_id = os.environ["GCP_WIF_PROVIDER"]
    service_account = os.environ["GCP_FEDERATED_SERVICE_ACCOUNT"]
    token = os.environ["GITLAB_OIDC_TOKEN"]

    token_path = Path(os.environ.get("CI_PROJECT_DIR", ".")) / ".gitlab-oidc-token"
    credentials_path = (
        Path(os.environ.get("CI_PROJECT_DIR", ".")) / ".gcp-credentials.json"
    )
    token_path.write_text(token, encoding="utf-8")
    os.chmod(token_path, 0o600)
    audience = (
        f"//iam.googleapis.com/projects/{project_number}/locations/global/"
        f"workloadIdentityPools/{pool_id}/providers/{provider_id}"
    )
    credentials = {
        "type": "external_account",
        "audience": audience,
        "subject_token_type": "urn:ietf:params:oauth:token-type:jwt",
        "token_url": "https://sts.googleapis.com/v1/token",
        "service_account_impersonation_url": (
            "https://iamcredentials.googleapis.com/v1/projects/-/serviceAccounts/"
            f"{service_account}:generateAccessToken"
        ),
        "credential_source": {
            "file": str(token_path.resolve()),
            "format": {"type": "text"},
        },
    }
    credentials_path.write_text(
        json.dumps(credentials, indent=2), encoding="utf-8"
    )
    os.chmod(credentials_path, 0o600)
    print("Credenciales ADC federadas listas; no se generó una llave permanente.")


if __name__ == "__main__":
    main()

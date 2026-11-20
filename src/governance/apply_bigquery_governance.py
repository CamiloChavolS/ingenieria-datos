"""Attach BigQuery column tags and country row policies to Gold tables."""

import os
import re

from google.cloud import bigquery


EMAIL_PATTERN = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+"


def _apply_policy_tags(client, project_id, table_name, sensitive_columns, tag_name):
    table_id = f"{project_id}.gold.{table_name}"
    table = client.get_table(table_id)
    schema = []
    found = set()

    for field in table.schema:
        representation = field.to_api_repr()
        if field.name in sensitive_columns:
            representation["policyTags"] = {"names": [tag_name]}
            found.add(field.name)
        schema.append(bigquery.SchemaField.from_api_repr(representation))

    missing = sensitive_columns - found
    if missing:
        raise ValueError(
            f"Faltan columnas sensibles {sorted(missing)} en {table_id}."
        )

    table.schema = schema
    client.update_table(table, ["schema"])
    return table_id


def _apply_row_policies(
    client,
    table_id,
    country_column,
    country,
    group,
    runtime,
    pipeline,
):
    policies = (
        (
            "pipeline_full_access",
            f"'serviceAccount:{pipeline}'",
            "TRUE",
        ),
        (
            "country_analyst_scope",
            f"'group:{group}', 'serviceAccount:{runtime}'",
            f"{country_column} = '{country}'",
        ),
    )
    for policy_name, grantees, filter_expression in policies:
        statement = f"""
            CREATE OR REPLACE ROW ACCESS POLICY {policy_name}
            ON `{table_id}`
            GRANT TO ({grantees})
            FILTER USING ({filter_expression})
        """
        client.query(statement).result()


def main():
    project_id = os.environ["GCP_PROJECT_ID"]
    tag_name = os.environ["BQ_ACCOUNT_ID_POLICY_TAG"]
    group = os.environ["GOVERNANCE_GROUP"]
    runtime = os.environ["CLOUD_RUN_RUNTIME_SERVICE_ACCOUNT"]
    pipeline = os.environ["GCP_PIPELINE_SERVICE_ACCOUNT"]
    country = os.getenv("GOVERNANCE_COUNTRY", "US").upper()

    if not re.fullmatch(r"[A-Z0-9_-]+", country):
        raise ValueError("GOVERNANCE_COUNTRY contiene caracteres inválidos.")
    for variable, identity in (
        ("GOVERNANCE_GROUP", group),
        ("CLOUD_RUN_RUNTIME_SERVICE_ACCOUNT", runtime),
        ("GCP_PIPELINE_SERVICE_ACCOUNT", pipeline),
    ):
        if not re.fullmatch(EMAIL_PATTERN, identity):
            raise ValueError(f"{variable} no es una identidad válida.")

    client = bigquery.Client(project=project_id)
    protected_tables = {
        "dim_account": {"account_id", "account_name"},
        "fct_customer_churn": {"account_id"},
        "mart_customer_churn": {"account_id", "account_name"},
    }
    row_filter_columns = {
        "dim_account": "country_key",
        "fct_customer_churn": "country_key",
        "mart_customer_churn": "country",
    }

    for table_name, sensitive_columns in protected_tables.items():
        table_id = _apply_policy_tags(
            client,
            project_id,
            table_name,
            sensitive_columns,
            tag_name,
        )
        _apply_row_policies(
            client,
            table_id,
            row_filter_columns[table_name],
            country,
            group,
            runtime,
            pipeline,
        )
        print(f"Gobernanza aplicada a {table_id}.")


if __name__ == "__main__":
    main()

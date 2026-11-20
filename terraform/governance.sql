-- Reference DDL for row access only. The CI job executes
-- src/governance/apply_bigquery_governance.py, which also attaches policy tags.
-- Replace project, group and service account placeholders before use.
-- US is present in the current synthetic country snapshot; set the matching
-- GOVERNANCE_COUNTRY for the intended data scope.

CREATE OR REPLACE ROW ACCESS POLICY pipeline_full_access
ON `PROJECT_ID.gold.dim_account`
GRANT TO ('serviceAccount:PIPELINE_SERVICE_ACCOUNT')
FILTER USING (TRUE);

CREATE OR REPLACE ROW ACCESS POLICY country_analyst_scope
ON `PROJECT_ID.gold.dim_account`
GRANT TO (
  'group:ANALYSTS_GROUP',
  'serviceAccount:RUNTIME_SERVICE_ACCOUNT'
)
FILTER USING (country_key = 'US');

CREATE OR REPLACE ROW ACCESS POLICY pipeline_full_access
ON `PROJECT_ID.gold.fct_customer_churn`
GRANT TO ('serviceAccount:PIPELINE_SERVICE_ACCOUNT')
FILTER USING (TRUE);

CREATE OR REPLACE ROW ACCESS POLICY country_analyst_scope
ON `PROJECT_ID.gold.fct_customer_churn`
GRANT TO (
  'group:ANALYSTS_GROUP',
  'serviceAccount:RUNTIME_SERVICE_ACCOUNT'
)
FILTER USING (country_key = 'US');

CREATE OR REPLACE ROW ACCESS POLICY pipeline_full_access
ON `PROJECT_ID.gold.mart_customer_churn`
GRANT TO ('serviceAccount:PIPELINE_SERVICE_ACCOUNT')
FILTER USING (TRUE);

CREATE OR REPLACE ROW ACCESS POLICY country_analyst_scope
ON `PROJECT_ID.gold.mart_customer_churn`
GRANT TO (
  'group:ANALYSTS_GROUP',
  'serviceAccount:RUNTIME_SERVICE_ACCOUNT'
)
FILTER USING (country = 'US');

{{ config(materialized='table') }}

select
    account_id,
    coalesce(nullif(trim(account_name), ''), 'Unknown') as account_name,
    coalesce(nullif(trim(industry), ''), 'Unknown') as industry,
    coalesce(upper(nullif(trim(country), '')), 'UNKNOWN') as country_key
from {{ ref('fct_customer_churn_summary') }}

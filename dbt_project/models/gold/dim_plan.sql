{{ config(materialized='table') }}

with normalized_plans as (
    select
        coalesce(nullif(trim(plan_tier), ''), 'Unknown') as plan_tier
    from {{ ref('fct_customer_churn_summary') }}
)

select
    upper(plan_tier) as plan_key,
    max(plan_tier) as plan_tier
from normalized_plans
group by upper(plan_tier)

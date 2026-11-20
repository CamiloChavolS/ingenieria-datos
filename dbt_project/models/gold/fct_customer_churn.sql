{{ config(materialized='table') }}

select
    account_id,
    upper(coalesce(nullif(trim(plan_tier), ''), 'Unknown')) as plan_key,
    coalesce(upper(nullif(trim(country), '')), 'UNKNOWN') as country_key,
    coalesce(monthly_recurring_revenue, 0) as monthly_recurring_revenue,
    is_churned,
    case when is_churned = 0 then 1 else 0 end as is_active,
    churn_date,
    total_feature_usage,
    total_usage_errors,
    last_activity_date,
    total_support_tickets,
    avg_resolution_time_hours,
    avg_satisfaction_score
from {{ ref('fct_customer_churn_summary') }}

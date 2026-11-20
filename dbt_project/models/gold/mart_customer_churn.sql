select
    fact.account_id,
    account.account_name,
    account.industry,
    country.country_code as country,
    plan.plan_tier,
    fact.monthly_recurring_revenue,
    fact.is_churned,
    fact.is_active,
    fact.churn_date,
    fact.total_feature_usage,
    fact.total_usage_errors,
    fact.last_activity_date,
    fact.total_support_tickets,
    fact.avg_resolution_time_hours,
    fact.avg_satisfaction_score
from {{ ref('fct_customer_churn') }} as fact
inner join {{ ref('dim_account') }} as account
    on fact.account_id = account.account_id
inner join {{ ref('dim_plan') }} as plan
    on fact.plan_key = plan.plan_key
inner join {{ ref('dim_country') }} as country
    on fact.country_key = country.country_key

select
    count(*) as total_customers,
    count(case when is_active = 1 then 1 end) as active_customers,
    count(case when is_churned = 1 then 1 end) as churned_customers,
    round(
        100.0 * count(case when is_churned = 1 then 1 end)
        / nullif(count(*), 0),
        2
    ) as churn_rate_pct,
    round(
        100.0 * count(case when is_active = 1 then 1 end)
        / nullif(count(*), 0),
        2
    ) as retention_rate_pct,
    sum(case when is_active = 1 then monthly_recurring_revenue else 0 end)
        as active_mrr,
    avg(case when is_active = 1 then monthly_recurring_revenue end)
        as avg_active_mrr
from {{ ref('mart_customer_churn') }}

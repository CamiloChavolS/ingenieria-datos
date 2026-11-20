{{ config(materialized='table') }}

with accounts as (
    select * from {{ ref('stg_accounts') }}
),

ranked_subscriptions as (
    select
        *,
        row_number() over (
            partition by account_id
            order by start_date desc nulls last, subscription_id desc
        ) as subscription_rank
    from {{ ref('stg_subscriptions') }}
),

latest_subscriptions as (
    select *
    from ranked_subscriptions
    where subscription_rank = 1
),

churn_events as (
    select
        account_id,
        max(case when not is_reactivation then churn_date end) as last_churn_date
    from {{ ref('stg_churn_events') }}
    group by account_id
),

usage_by_account as (
    select
        subscriptions.account_id,
        sum(coalesce(feature_usage.usage_count, 0)) as total_feature_usage,
        sum(coalesce(feature_usage.error_count, 0)) as total_usage_errors,
        max(feature_usage.usage_date) as last_activity_date
    from {{ ref('stg_feature_usage') }} as feature_usage
    inner join {{ ref('stg_subscriptions') }} as subscriptions
        on feature_usage.subscription_id = subscriptions.subscription_id
    group by subscriptions.account_id
),

support_by_account as (
    select
        account_id,
        count(*) as total_support_tickets,
        avg(resolution_time_hours) as avg_resolution_time_hours,
        avg(satisfaction_score) as avg_satisfaction_score
    from {{ ref('stg_support_tickets') }}
    group by account_id
)

select
    accounts.account_id,
    accounts.account_name,
    accounts.industry,
    accounts.country,
    latest_subscriptions.plan_tier,
    latest_subscriptions.mrr_amount as monthly_recurring_revenue,
    case when accounts.churn_flag then 1 else 0 end as is_churned,
    case
        when accounts.churn_flag then churn_events.last_churn_date
        else null
    end as churn_date,
    coalesce(usage_by_account.total_feature_usage, 0) as total_feature_usage,
    coalesce(usage_by_account.total_usage_errors, 0) as total_usage_errors,
    usage_by_account.last_activity_date,
    coalesce(support_by_account.total_support_tickets, 0) as total_support_tickets,
    support_by_account.avg_resolution_time_hours,
    support_by_account.avg_satisfaction_score
from accounts
left join latest_subscriptions
    on accounts.account_id = latest_subscriptions.account_id
left join churn_events
    on accounts.account_id = churn_events.account_id
left join usage_by_account
    on accounts.account_id = usage_by_account.account_id
left join support_by_account
    on accounts.account_id = support_by_account.account_id

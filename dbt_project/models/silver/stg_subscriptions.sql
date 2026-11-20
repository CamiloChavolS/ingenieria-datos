select
    nullif(trim({{ cast_string('subscription_id') }}), '') as subscription_id,
    nullif(trim({{ cast_string('account_id') }}), '') as account_id,
    {{ cast_date("nullif(trim(" ~ cast_string("start_date") ~ "), '')") }}
        as start_date,
    {{ cast_date("nullif(trim(" ~ cast_string("end_date") ~ "), '')") }}
        as end_date,
    nullif(trim({{ cast_string('plan_tier') }}), '') as plan_tier,
    {{ cast_integer("nullif(trim(" ~ cast_string("seats") ~ "), '')") }}
        as seats,
    {{ cast_numeric("nullif(trim(" ~ cast_string("mrr_amount") ~ "), '')") }}
        as mrr_amount,
    {{ cast_numeric("nullif(trim(" ~ cast_string("arr_amount") ~ "), '')") }}
        as arr_amount,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("is_trial") ~ "), '')") }},
        false
    ) as is_trial,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("upgrade_flag") ~ "), '')") }},
        false
    ) as upgrade_flag,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("downgrade_flag") ~ "), '')") }},
        false
    ) as downgrade_flag,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("churn_flag") ~ "), '')") }},
        false
    ) as churn_flag,
    lower(nullif(trim({{ cast_string('billing_frequency') }}), ''))
        as billing_frequency,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("auto_renew_flag") ~ "), '')") }},
        false
    ) as auto_renew_flag
from {{ source('bronze', 'subscriptions') }}
where nullif(trim({{ cast_string('subscription_id') }}), '') is not null

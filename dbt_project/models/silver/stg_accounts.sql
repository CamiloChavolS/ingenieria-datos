select
    nullif(trim({{ cast_string('account_id') }}), '') as account_id,
    nullif(trim({{ cast_string('account_name') }}), '') as account_name,
    nullif(trim({{ cast_string('industry') }}), '') as industry,
    upper(nullif(trim({{ cast_string('country') }}), '')) as country,
    {{ cast_date("nullif(trim(" ~ cast_string("signup_date") ~ "), '')") }}
        as signup_date,
    nullif(trim({{ cast_string('referral_source') }}), '') as referral_source,
    nullif(trim({{ cast_string('plan_tier') }}), '') as plan_tier,
    {{ cast_integer("nullif(trim(" ~ cast_string("seats") ~ "), '')") }}
        as seats,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("is_trial") ~ "), '')") }},
        false
    ) as is_trial,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("churn_flag") ~ "), '')") }},
        false
    ) as churn_flag
from {{ source('bronze', 'accounts') }}
where nullif(trim({{ cast_string('account_id') }}), '') is not null

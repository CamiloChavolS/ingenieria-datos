select
    nullif(trim({{ cast_string('churn_event_id') }}), '') as churn_event_id,
    nullif(trim({{ cast_string('account_id') }}), '') as account_id,
    {{ cast_date("nullif(trim(" ~ cast_string("churn_date") ~ "), '')") }}
        as churn_date,
    lower(nullif(trim({{ cast_string('reason_code') }}), '')) as reason_code,
    {{ cast_numeric("nullif(trim(" ~ cast_string("refund_amount_usd") ~ "), '')") }}
        as refund_amount_usd,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("preceding_upgrade_flag") ~ "), '')") }},
        false
    )
        as preceding_upgrade_flag,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("preceding_downgrade_flag") ~ "), '')") }},
        false
    )
        as preceding_downgrade_flag,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("is_reactivation") ~ "), '')") }},
        false
    )
        as is_reactivation,
    nullif(trim({{ cast_string('feedback_text') }}), '') as feedback_text
from {{ source('bronze', 'churn_events') }}
where nullif(trim({{ cast_string('churn_event_id') }}), '') is not null

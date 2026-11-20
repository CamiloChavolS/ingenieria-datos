select
    nullif(trim({{ cast_string('usage_id') }}), '') as usage_id,
    nullif(trim({{ cast_string('subscription_id') }}), '') as subscription_id,
    {{ cast_date("nullif(trim(" ~ cast_string("usage_date") ~ "), '')") }}
        as usage_date,
    nullif(trim({{ cast_string('feature_name') }}), '') as feature_name,
    {{ cast_integer("nullif(trim(" ~ cast_string("usage_count") ~ "), '')") }}
        as usage_count,
    {{ cast_integer("nullif(trim(" ~ cast_string("usage_duration_secs") ~ "), '')") }}
        as usage_duration_secs,
    {{ cast_integer("nullif(trim(" ~ cast_string("error_count") ~ "), '')") }}
        as error_count,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("is_beta_feature") ~ "), '')") }},
        false
    )
        as is_beta_feature
from {{ source('bronze', 'feature_usage') }}
where nullif(trim({{ cast_string('usage_id') }}), '') is not null

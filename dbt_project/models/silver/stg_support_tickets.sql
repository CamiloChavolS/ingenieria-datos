select
    nullif(trim({{ cast_string('ticket_id') }}), '') as ticket_id,
    nullif(trim({{ cast_string('account_id') }}), '') as account_id,
    {{ cast_timestamp("nullif(trim(" ~ cast_string("submitted_at") ~ "), '')") }}
        as submitted_at,
    {{ cast_timestamp("nullif(trim(" ~ cast_string("closed_at") ~ "), '')") }}
        as closed_at,
    {{ cast_numeric("nullif(trim(" ~ cast_string("resolution_time_hours") ~ "), '')") }}
        as resolution_time_hours,
    lower(nullif(trim({{ cast_string('priority') }}), '')) as priority,
    {{ cast_integer("nullif(trim(" ~ cast_string("first_response_time_minutes") ~ "), '')") }}
        as first_response_time_minutes,
    {{ cast_numeric("nullif(trim(" ~ cast_string("satisfaction_score") ~ "), '')", 4, 2) }}
        as satisfaction_score,
    coalesce(
        {{ cast_boolean("nullif(trim(" ~ cast_string("escalation_flag") ~ "), '')") }},
        false
    )
        as escalation_flag
from {{ source('bronze', 'support_tickets') }}
where nullif(trim({{ cast_string('ticket_id') }}), '') is not null

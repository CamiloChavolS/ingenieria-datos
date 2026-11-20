{{ config(enabled=env_var('ENABLE_GENAI_ENRICHMENT', 'false') | lower == 'true') }}

select
    theme,
    sentiment,
    count(*) as feedback_count,
    round(avg(confidence), 3) as average_confidence
from {{ source('silver_ai', 'churn_feedback_enrichment') }}
group by theme, sentiment

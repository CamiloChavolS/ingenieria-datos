{{ config(materialized='table') }}

select distinct
    coalesce(upper(nullif(trim(country), '')), 'UNKNOWN') as country_key,
    coalesce(upper(nullif(trim(country), '')), 'UNKNOWN') as country_code,
    case coalesce(upper(nullif(trim(country), '')), 'UNKNOWN')
        when 'AU' then 'Australia'
        when 'CA' then 'Canada'
        when 'DE' then 'Germany'
        when 'FR' then 'France'
        when 'IN' then 'India'
        when 'UK' then 'United Kingdom'
        when 'US' then 'United States'
        else 'Unknown'
    end as country_name
from {{ ref('fct_customer_churn_summary') }}

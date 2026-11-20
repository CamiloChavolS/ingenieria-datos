{% macro cast_string(expression) -%}
    {{ return(adapter.dispatch('cast_string')(expression)) }}
{%- endmacro %}

{% macro default__cast_string(expression) -%}
    CAST({{ expression }} AS TEXT)
{%- endmacro %}

{% macro bigquery__cast_string(expression) -%}
    CAST({{ expression }} AS STRING)
{%- endmacro %}

{% macro cast_boolean(expression) -%}
    {{ return(adapter.dispatch('cast_boolean')(expression)) }}
{%- endmacro %}

{% macro default__cast_boolean(expression) -%}
    CAST({{ expression }} AS BOOLEAN)
{%- endmacro %}

{% macro bigquery__cast_boolean(expression) -%}
    CAST({{ expression }} AS BOOL)
{%- endmacro %}

{% macro cast_integer(expression) -%}
    {{ return(adapter.dispatch('cast_integer')(expression)) }}
{%- endmacro %}

{% macro default__cast_integer(expression) -%}
    CAST({{ expression }} AS INTEGER)
{%- endmacro %}

{% macro bigquery__cast_integer(expression) -%}
    CAST({{ expression }} AS INT64)
{%- endmacro %}

{% macro cast_date(expression) -%}
    CAST({{ expression }} AS DATE)
{%- endmacro %}

{% macro cast_timestamp(expression) -%}
    CAST({{ expression }} AS TIMESTAMP)
{%- endmacro %}

{% macro cast_numeric(expression, precision=12, scale=2) -%}
    {{ return(adapter.dispatch('cast_numeric')(expression, precision, scale)) }}
{%- endmacro %}

{% macro default__cast_numeric(expression, precision, scale) -%}
    CAST({{ expression }} AS NUMERIC({{ precision }}, {{ scale }}))
{%- endmacro %}

{% macro bigquery__cast_numeric(expression, precision, scale) -%}
    ROUND(CAST({{ expression }} AS NUMERIC), {{ scale }})
{%- endmacro %}

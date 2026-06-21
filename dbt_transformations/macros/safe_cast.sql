{% macro safe_cast_numeric(expression) %}
    (
        case
            when nullif(trim(cast({{ expression }} as varchar)), '') is null then null
            when trim(cast({{ expression }} as varchar)) ~ '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$'
                then cast(trim(cast({{ expression }} as varchar)) as numeric)
            else null
        end
    )
{% endmacro %}

{% macro safe_cast_numeric_column(column_name, null_value=none) %}
    {% set quoted_column = adapter.quote(column_name) %}
    {% if null_value is none %}
        {{ safe_cast_numeric(quoted_column) }}
    {% else %}
        {{ safe_cast_numeric("nullif(trim(" ~ quoted_column ~ "), '" ~ null_value ~ "')") }}
    {% endif %}
{% endmacro %}

{% macro project_metric(column_name) %}
    {{ safe_cast_numeric("replace(" ~ adapter.quote(column_name) ~ ", '.0', '')") }}
{% endmacro %}

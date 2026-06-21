{% macro parquet(nome_arquivo) %}
    {{ source('raw', nome_arquivo) }}
{% endmacro %}

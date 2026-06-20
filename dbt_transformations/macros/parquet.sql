{% macro parquet(nome_arquivo) %}
    read_parquet('../data/raw/{{ nome_arquivo }}.parquet')
{% endmacro %}

{{ config(materialized='table') }}

{% set anos = [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023] %}

WITH

dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_rede AS (
    SELECT * FROM {{ ref('dim_rede') }}
),

stg_ideb_wide AS (
    SELECT * FROM {{ ref('stg_ideb') }}
),

unpivot AS (
    {% for ano in anos %}
    SELECT
        id_municipio,
        nome_rede,
        {{ ano }} AS ano,
        vl_observado_{{ ano }} AS ideb_observado,
        {% if ano >= 2007 and ano <= 2021 %}
        vl_projecao_{{ ano }} AS ideb_projecao,
        {% else %}
        CAST(NULL AS NUMERIC) AS ideb_projecao,
        {% endif %}
        ROUND(vl_nota_media_{{ ano }}, 2) AS nota_media_saeb,
        ROUND(vl_nota_matematica_{{ ano }}, 2) AS nota_matematica_saeb,
        ROUND(vl_nota_portugues_{{ ano }}, 2) AS nota_portugues_saeb,
        vl_aprovacao_{{ ano }}_si / 100.0 AS taxa_aprovacao_series_iniciais,
        vl_aprovacao_{{ ano }}_si_4 / 100.0 AS taxa_aprovacao_si_4ano,
        vl_aprovacao_{{ ano }}_1 / 100.0 AS taxa_aprovacao_1ano,
        vl_aprovacao_{{ ano }}_2 / 100.0 AS taxa_aprovacao_2ano,
        vl_aprovacao_{{ ano }}_3 / 100.0 AS taxa_aprovacao_3ano,
        vl_aprovacao_{{ ano }}_4 / 100.0 AS taxa_aprovacao_4ano,
        vl_indicador_rend_{{ ano }} AS indicador_rendimento
    FROM stg_ideb_wide
    {% if not loop.last %} UNION ALL {% endif %}
    {% endfor %}
),

fato_ideb AS (
    SELECT
        d.sk_localidade,
        r.sk_rede,
        u.ano,
        u.ideb_observado,
        u.ideb_projecao,
        u.nota_media_saeb,
        u.nota_matematica_saeb,
        u.nota_portugues_saeb,
        u.taxa_aprovacao_series_iniciais,
        u.taxa_aprovacao_si_4ano,
        u.taxa_aprovacao_1ano,
        u.taxa_aprovacao_2ano,
        u.taxa_aprovacao_3ano,
        u.taxa_aprovacao_4ano,
        u.indicador_rendimento
    FROM unpivot u
    INNER JOIN dim_rede r
        ON u.nome_rede = r.nome_rede
    INNER JOIN dim_localidade d
        ON u.id_municipio = d.id_municipio
    WHERE u.ideb_observado IS NOT NULL
       OR u.ideb_projecao IS NOT NULL
       OR u.nota_media_saeb IS NOT NULL
       OR u.nota_matematica_saeb IS NOT NULL
       OR u.nota_portugues_saeb IS NOT NULL
       OR u.taxa_aprovacao_series_iniciais IS NOT NULL
       OR u.taxa_aprovacao_si_4ano IS NOT NULL
       OR u.taxa_aprovacao_1ano IS NOT NULL
       OR u.taxa_aprovacao_2ano IS NOT NULL
       OR u.taxa_aprovacao_3ano IS NOT NULL
       OR u.taxa_aprovacao_4ano IS NOT NULL
       OR u.indicador_rendimento IS NOT NULL
)

SELECT * FROM fato_ideb

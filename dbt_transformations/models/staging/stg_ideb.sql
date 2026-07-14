WITH source AS (
    SELECT * FROM {{ source('raw', 'ideb_municipios') }}
),

{% set anos = [2005, 2007, 2009, 2011, 2013, 2015, 2017, 2019, 2021, 2023] %}

clean AS (
    SELECT
        CAST(CAST("CO_MUNICIPIO" AS NUMERIC) AS INTEGER) AS id_municipio,
        UPPER(TRIM("NO_MUNICIPIO")) AS nome_municipio,
        UPPER(TRIM("SG_UF")) AS sigla_uf,
        UPPER(TRIM("REDE")) AS nome_rede

        {% for ano in anos %}
        ,{{ safe_cast_numeric_column('VL_OBSERVADO_' ~ ano, '-') }} AS vl_observado_{{ ano }}
        {% if ano >= 2007 and ano <= 2021 %}
        ,{{ safe_cast_numeric_column('VL_PROJECAO_' ~ ano, '-') }} AS vl_projecao_{{ ano }}
        {% endif %}
        ,{{ safe_cast_numeric_column('VL_NOTA_MEDIA_' ~ ano, '-') }} AS vl_nota_media_{{ ano }}
        ,{{ safe_cast_numeric_column('VL_NOTA_MATEMATICA_' ~ ano, '-') }} AS vl_nota_matematica_{{ ano }}
        ,{{ safe_cast_numeric_column('VL_NOTA_PORTUGUES_' ~ ano, '-') }} AS vl_nota_portugues_{{ ano }}
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_SI', '-') }} AS vl_aprovacao_{{ ano }}_si
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_SI_4', '-') }} AS vl_aprovacao_{{ ano }}_si_4
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_1', '-') }} AS vl_aprovacao_{{ ano }}_1
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_2', '-') }} AS vl_aprovacao_{{ ano }}_2
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_3', '-') }} AS vl_aprovacao_{{ ano }}_3
        ,{{ safe_cast_numeric_column('VL_APROVACAO_' ~ ano ~ '_4', '-') }} AS vl_aprovacao_{{ ano }}_4
        ,{{ safe_cast_numeric_column('VL_INDICADOR_REND_' ~ ano, '-') }} AS vl_indicador_rend_{{ ano }}
        {% endfor %}

    FROM source
    WHERE "CO_MUNICIPIO" IS NOT NULL
      AND "REDE" IS NOT NULL
      AND TRIM("REDE") != ''
),

filtered AS (
    SELECT * FROM clean
    {% for ano in anos %}
    {% if loop.first %}WHERE ({% endif %}
    (vl_observado_{{ ano }} IS NOT NULL
        OR vl_nota_media_{{ ano }} IS NOT NULL
        OR vl_nota_matematica_{{ ano }} IS NOT NULL
        OR vl_nota_portugues_{{ ano }} IS NOT NULL
        OR vl_aprovacao_{{ ano }}_si IS NOT NULL
        OR vl_aprovacao_{{ ano }}_si_4 IS NOT NULL
        OR vl_aprovacao_{{ ano }}_1 IS NOT NULL
        OR vl_aprovacao_{{ ano }}_2 IS NOT NULL
        OR vl_aprovacao_{{ ano }}_3 IS NOT NULL
        OR vl_aprovacao_{{ ano }}_4 IS NOT NULL
        OR vl_indicador_rend_{{ ano }} IS NOT NULL
        {% if ano >= 2007 and ano <= 2021 %}
        OR vl_projecao_{{ ano }} IS NOT NULL
        {% endif %})
    {% if not loop.last %}OR{% endif %}
    {% if loop.last %}){% endif %}
    {% endfor %}
)

SELECT * FROM filtered

WITH source AS (
    SELECT * FROM {{ source('raw', 'taxa_distorcao') }}
),

transformacao AS (
    SELECT
        CAST("NU_ANO_CENSO" AS INTEGER) AS ano_competencia,

        CAST(CAST(NULLIF("CO_MUNICIPIO", '') AS NUMERIC) AS INTEGER) AS id_municipio,

        UPPER(TRIM("SG_UF")) AS sigla_uf,
        UPPER(TRIM("NO_MUNICIPIO")) AS nome_municipio,

        UPPER(TRIM("NO_CATEGORIA")) AS categoria_localidade,
        UPPER(TRIM("NO_DEPENDENCIA")) AS dependencia_administrativa,

        {{ safe_cast_numeric_column('FUN_CAT_0', '--') }} / 100.0 AS taxa_distorcao_ensino_fundamental,
        {{ safe_cast_numeric_column('MED_CAT_0', '--') }} / 100.0 AS taxa_distorcao_ensino_medio

    FROM source
    WHERE "CO_MUNICIPIO" IS NOT NULL
      AND (UPPER(TRIM("NO_CATEGORIA")) != 'TOTAL'
        OR UPPER(TRIM("NO_DEPENDENCIA")) != 'TOTAL')
)

SELECT * FROM transformacao
WHERE COALESCE(taxa_distorcao_ensino_fundamental, 0) != 0
   OR COALESCE(taxa_distorcao_ensino_medio, 0) != 0

WITH source AS (
    SELECT * FROM {{ source('raw', 'taxa_distorcao') }}
),

transformacao AS (
    SELECT
        CAST("NU_ANO_CENSO" AS INTEGER) AS ano_competencia,
        
        -- Higienização da chave: Conversão de float para inteiro
        CAST("CO_MUNICIPIO" AS INTEGER) AS id_municipio,
        
        UPPER(TRIM("SG_UF")) AS sigla_uf,
        UPPER(TRIM("NO_MUNICIPIO")) AS nome_municipio,
        
        -- Atributos dimensionais que justificam as múltiplas linhas por município
        UPPER(TRIM("NO_CATEGORIA")) AS categoria_localidade,
        UPPER(TRIM("NO_DEPENDENCIA")) AS dependencia_administrativa,
        
        -- Higienização de métricas: Tratamento do caractere '--' e conversão para decimal
        TRY_CAST(NULLIF(TRIM("FUN_CAT_0"), '--') AS NUMERIC) AS taxa_distorcao_ensino_fundamental,
        TRY_CAST(NULLIF(TRIM("MED_CAT_0"), '--') AS NUMERIC) AS taxa_distorcao_ensino_medio

    FROM source
    WHERE "CO_MUNICIPIO" IS NOT NULL
)

SELECT * FROM transformacao
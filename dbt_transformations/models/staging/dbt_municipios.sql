WITH source AS (
    SELECT * FROM {{ parquet('dtb_municipios') }}
),

dtb AS (
    SELECT
        CAST("Código Município Completo" AS INTEGER) AS id_municipio,
        UPPER(TRIM("Nome_Município")) AS nome_municipio,
        CAST("UF" AS INTEGER) AS id_uf,
        UPPER(TRIM("sigla_uf")) AS sigla_uf,
        UPPER(TRIM("Nome_UF")) AS nome_uf,
        CAST("Região Geográfica Imediata" AS INTEGER)  AS id_regiao_geografica_imediata,
        UPPER(TRIM("Nome Região Geográfica Imediata")) AS nome_regiao_geografica_imediata
    FROM source
    WHERE "Código Município Completo" IS NOT NULL
)

SELECT * FROM dtb
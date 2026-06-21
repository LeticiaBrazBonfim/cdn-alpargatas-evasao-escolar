{{ config(materialized='table') }}

WITH staging_dtb AS (
    SELECT * FROM {{ ref('stg_dtb') }}
),

dim_localidade AS (
    SELECT
        -- Surrogate Key: numérica, sequencial, ordenada por id_municipio
        ROW_NUMBER() OVER (ORDER BY id_municipio) AS sk_localidade,

        -- Business Keys (Chaves Naturais)
        id_municipio,
        CONCAT(CAST(id_municipio AS VARCHAR), ' - ', nome_municipio) AS id_nome_municipio,
        nome_municipio,

        -- Dimensões Geográficas
        id_uf,
        CONCAT(CAST(id_uf AS VARCHAR), ' - ', nome_uf) AS id_nome_uf,
        nome_uf,

        id_regiao_geografica_imediata,
        CONCAT(CAST(id_regiao_geografica_imediata AS VARCHAR), ' - ', nome_regiao_geografica_imediata) AS id_nome_regiao_geografica_imediata,
        nome_regiao_geografica_imediata
    FROM staging_dtb
)

SELECT * FROM dim_localidade
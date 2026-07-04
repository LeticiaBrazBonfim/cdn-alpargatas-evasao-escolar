{{ config(materialized='table') }}

WITH staging_dtb AS (
    SELECT * FROM {{ ref('stg_dtb') }}
),

dedup AS (
    SELECT DISTINCT
        id_municipio,
        nome_municipio,

        id_uf,
        nome_uf,

        id_regiao_geografica_imediata,
        nome_regiao_geografica_imediata
    FROM staging_dtb
),

dim_localidade AS (
    SELECT
        MD5(CAST(id_municipio AS VARCHAR)) AS sk_localidade,

        id_municipio,
        CONCAT(CAST(id_municipio AS VARCHAR), ' - ', nome_municipio) AS id_nome_municipio,
        nome_municipio,

        id_uf,
        CONCAT(CAST(id_uf AS VARCHAR), ' - ', nome_uf) AS id_nome_uf,
        nome_uf,

        id_regiao_geografica_imediata,
        CONCAT(CAST(id_regiao_geografica_imediata AS VARCHAR), ' - ', nome_regiao_geografica_imediata) AS id_nome_regiao_geografica_imediata,
        nome_regiao_geografica_imediata
    FROM dedup
)

SELECT * FROM dim_localidade

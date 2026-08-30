{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

projetos_ia AS (
    SELECT * FROM {{ ref('stg_projetos_ia') }}
),

municipios_com_projeto AS (
    SELECT
        p.id_municipio,
        p.ano_competencia AS ano,
        SUM(p.total_projetos_ia) AS quantidade_projetos,
        SUM(p.total_beneficiados) AS quantidade_beneficiados
    FROM projetos_ia AS p
    WHERE p.id_municipio IS NOT NULL
    GROUP BY
        p.id_municipio,
        p.ano_competencia
),

fato_com_sk AS (
    SELECT
        d.sk_localidade,
        c.sk_calendario,
        m.ano,
        m.quantidade_projetos,
        m.quantidade_beneficiados
    FROM municipios_com_projeto m
    INNER JOIN dim_localidade d
        ON m.id_municipio = d.id_municipio
    INNER JOIN dim_calendario c
        ON m.ano = c.ano_referencia
)

SELECT * FROM fato_com_sk

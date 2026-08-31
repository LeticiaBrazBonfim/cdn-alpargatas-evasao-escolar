{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

projetos_ia AS (
    SELECT * FROM {{ ref('projetos_ia') }}
),

municipios_com_projeto AS (
    SELECT
        p.id_municipio,
        p.ano_competencia AS ano,
        SUM(COALESCE(p.projetos_1, 0) + COALESCE(p.projetos_2, 0) + COALESCE(p.projetos_3, 0)
          + COALESCE(p.projetos_4, 0) + COALESCE(p.projetos_5, 0) + COALESCE(p.projetos_6, 0)) AS quantidade_projetos,
        SUM(COALESCE(p.beneficiados_1, 0) + COALESCE(p.beneficiados_2, 0) + COALESCE(p.beneficiados_3, 0)
          + COALESCE(p.beneficiados_4, 0) + COALESCE(p.beneficiados_5, 0) + COALESCE(p.beneficiados_6, 0)) AS quantidade_beneficiados
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

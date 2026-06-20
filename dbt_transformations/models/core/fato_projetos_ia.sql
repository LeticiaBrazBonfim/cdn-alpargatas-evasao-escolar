{{ config(materialized='table') }}

WITH 
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
)

SELECT
    id_municipio,
    ano,
    quantidade_projetos,
    quantidade_beneficiados
FROM municipios_com_projeto

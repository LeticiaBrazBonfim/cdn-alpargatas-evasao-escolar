{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

taxa_distorcao AS (
    SELECT * FROM {{ ref('stg_taxa_distorcao') }}
),

fato_taxa_distorcao AS (
    SELECT
        -- Chave Estrangeira (Dimensão)
        d.sk_localidade,

        -- Granularidade Temporal
        t.ano_competencia AS ano,

        -- Dimensões Analíticas
        t.categoria_localidade,
        t.dependencia_administrativa,

        -- Métricas: Taxas de Distorção Idade-Série
        t.taxa_distorcao_ensino_fundamental,
        t.taxa_distorcao_ensino_medio
    FROM taxa_distorcao t
    INNER JOIN dim_localidade d
        ON t.id_municipio = d.id_municipio
)

SELECT * FROM fato_taxa_distorcao

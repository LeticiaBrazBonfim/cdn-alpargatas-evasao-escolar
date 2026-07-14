{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

taxa_distorcao AS (
    SELECT * FROM {{ ref('taxa_distorcao') }}
),

fato AS (
    SELECT
        d.sk_localidade,
        c.sk_calendario,
        t.taxa_distorcao_ensino_fundamental,
        t.taxa_distorcao_ensino_medio
    FROM taxa_distorcao t
    INNER JOIN dim_localidade d
        ON t.id_municipio = d.id_municipio
    INNER JOIN dim_calendario c
        ON t.ano_competencia = c.ano_referencia
    WHERE t.categoria_localidade = 'TOTAL'
      AND t.dependencia_administrativa = 'TOTAL'
      AND (COALESCE(t.taxa_distorcao_ensino_fundamental, 0) != 0
        OR COALESCE(t.taxa_distorcao_ensino_medio, 0) != 0)
)

SELECT * FROM fato
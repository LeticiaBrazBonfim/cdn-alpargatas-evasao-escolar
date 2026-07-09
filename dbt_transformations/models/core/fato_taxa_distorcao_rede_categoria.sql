{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_rede AS (
    SELECT * FROM {{ ref('dim_rede') }}
),

taxa_distorcao AS (
    SELECT * FROM {{ ref('stg_taxa_distorcao') }}
    WHERE categoria_localidade != 'TOTAL'
       OR dependencia_administrativa != 'TOTAL'
),

fato AS (
    SELECT
        d.sk_localidade,
        COALESCE(r.sk_rede, MD5('DESCONHECIDO')) AS sk_rede,
        t.ano_competencia AS ano,
        t.categoria_localidade,
        t.taxa_distorcao_ensino_fundamental,
        t.taxa_distorcao_ensino_medio
    FROM taxa_distorcao t
    INNER JOIN dim_localidade d
        ON t.id_municipio = d.id_municipio
    LEFT JOIN dim_rede r
        ON UPPER(TRIM(t.dependencia_administrativa)) = r.nome_rede
)

SELECT * FROM fato
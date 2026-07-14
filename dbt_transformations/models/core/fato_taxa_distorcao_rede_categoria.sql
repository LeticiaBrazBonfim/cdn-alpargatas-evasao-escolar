{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

dim_rede AS (
    SELECT * FROM {{ ref('dim_rede') }}
),

taxa_distorcao AS (
    SELECT * FROM {{ ref('stg_taxa_distorcao_rede_categoria') }}
),

fato AS (
    SELECT
        d.sk_localidade,
        COALESCE(r.sk_rede, MD5('DESCONHECIDO')) AS sk_rede,
        c.sk_calendario,
        t.categoria_localidade,
        t.taxa_distorcao_ensino_fundamental,
        t.taxa_distorcao_ensino_medio
    FROM taxa_distorcao t
    INNER JOIN dim_localidade d
        ON t.id_municipio = d.id_municipio
    INNER JOIN dim_calendario c
        ON t.ano_competencia = c.ano_referencia
    LEFT JOIN dim_rede r
        ON UPPER(TRIM(t.dependencia_administrativa)) = r.nome_rede
    WHERE COALESCE(t.taxa_distorcao_ensino_fundamental, 0) != 0
       OR COALESCE(t.taxa_distorcao_ensino_medio, 0) != 0
)

SELECT * FROM fato
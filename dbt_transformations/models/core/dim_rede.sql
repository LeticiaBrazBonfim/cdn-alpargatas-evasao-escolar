{{ config(materialized='table') }}

WITH staging_rede AS (
    SELECT DISTINCT
        nome_rede
    FROM {{ ref('stg_ideb') }}
    WHERE nome_rede IS NOT NULL
      AND nome_rede IN ('ESTADUAL', 'MUNICIPAL', 'FEDERAL')
),

dim_rede AS (
    SELECT
        MD5(nome_rede) AS sk_rede,
        nome_rede,
        CASE nome_rede
            WHEN 'ESTADUAL'  THEN 2
            WHEN 'MUNICIPAL' THEN 4
            WHEN 'FEDERAL'   THEN 6
        END AS id_rede
    FROM staging_rede
)

SELECT
    sk_rede,
    nome_rede,
    id_rede,
    CONCAT(CAST(id_rede AS VARCHAR), ' - ', nome_rede) AS id_nome_rede
FROM dim_rede
ORDER BY id_rede

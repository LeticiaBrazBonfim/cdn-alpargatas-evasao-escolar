{{ config(materialized='table') }}

WITH staging_rede AS (
    SELECT UPPER(TRIM(nome_rede)) AS nome_rede
    FROM {{ ref('ideb_municipios') }}
    WHERE nome_rede IS NOT NULL

    UNION

    SELECT UPPER(TRIM(dependencia_administrativa))
    FROM {{ ref('taxa_distorcao') }}
    WHERE dependencia_administrativa IS NOT NULL
),

rede_padronizada AS (
    SELECT DISTINCT nome_rede
    FROM staging_rede
    WHERE nome_rede IN ('ESTADUAL', 'MUNICIPAL', 'FEDERAL', 'PRIVADA', 'TOTAL')
),

dim_rede AS (
    SELECT
        MD5(nome_rede) AS sk_rede,
        nome_rede,
        CASE nome_rede
            WHEN 'ESTADUAL'     THEN 2
            WHEN 'MUNICIPAL'    THEN 4
            WHEN 'FEDERAL'      THEN 6
            WHEN 'PRIVADA'      THEN 8
            WHEN 'TOTAL'        THEN 0
            WHEN 'DESCONHECIDO' THEN -1
        END AS id_rede
    FROM rede_padronizada

    UNION

    SELECT
        MD5('DESCONHECIDO') AS sk_rede,
        'DESCONHECIDO' AS nome_rede,
        CAST(-1 AS INTEGER) AS id_rede
)

SELECT
    sk_rede,
    nome_rede,
    id_rede,
    CASE
        WHEN id_rede IS NOT NULL THEN CONCAT(CAST(id_rede AS VARCHAR), ' - ', nome_rede)
        ELSE nome_rede
    END AS id_nome_rede
FROM dim_rede
ORDER BY id_rede NULLS LAST
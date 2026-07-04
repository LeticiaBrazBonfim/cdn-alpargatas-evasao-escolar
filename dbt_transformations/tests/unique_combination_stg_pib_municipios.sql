-- Test: unique combination of (id_municipio, ano) in stg_pib_municipios
-- Granularidade: 1 linha por município + ano

SELECT
    id_municipio,
    ano_competencia,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('stg_pib_municipios') }}
GROUP BY id_municipio, ano_competencia
HAVING COUNT(*) > 1

-- Test: unique combination of (id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa)
-- Granularidade: 1 linha por município + ano + categoria + dependência

SELECT
    id_municipio,
    ano_competencia,
    categoria_localidade,
    dependencia_administrativa,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('stg_taxa_distorcao') }}
GROUP BY id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa
HAVING COUNT(*) > 1

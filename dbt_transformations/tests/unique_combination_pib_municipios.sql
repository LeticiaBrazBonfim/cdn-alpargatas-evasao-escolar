SELECT
    id_municipio,
    ano_competencia,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('pib_municipios') }}
GROUP BY id_municipio, ano_competencia
HAVING COUNT(*) > 1

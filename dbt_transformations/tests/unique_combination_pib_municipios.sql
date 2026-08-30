SELECT
    id_municipio,
    ano,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('pib_municipios') }}
GROUP BY id_municipio, ano
HAVING COUNT(*) > 1

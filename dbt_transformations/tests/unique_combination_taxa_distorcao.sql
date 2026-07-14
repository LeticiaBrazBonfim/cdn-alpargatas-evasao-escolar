SELECT
    id_municipio,
    ano_competencia,
    categoria_localidade,
    dependencia_administrativa,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('taxa_distorcao') }}
GROUP BY id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa
HAVING COUNT(*) > 1

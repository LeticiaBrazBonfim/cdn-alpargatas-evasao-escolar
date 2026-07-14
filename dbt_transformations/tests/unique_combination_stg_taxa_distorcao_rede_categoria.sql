SELECT
    id_municipio,
    ano_competencia,
    categoria_localidade,
    dependencia_administrativa,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('stg_taxa_distorcao_rede_categoria') }}
GROUP BY id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa
HAVING COUNT(*) > 1

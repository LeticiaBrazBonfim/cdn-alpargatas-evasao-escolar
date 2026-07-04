-- Test: unique combination of (id_municipio, nome_rede) in stg_ideb
-- Granularidade wide: 1 linha por município + rede (dados bienais empilhados horizontalmente)

SELECT
    id_municipio,
    nome_rede,
    COUNT(*) AS qtd_duplicatas
FROM {{ ref('stg_ideb') }}
GROUP BY id_municipio, nome_rede
HAVING COUNT(*) > 1

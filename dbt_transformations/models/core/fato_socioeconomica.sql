{{ config(materialized='table') }}

WITH pib AS (
    SELECT * FROM {{ ref('stg_pib_municipios') }}
),

fato_socioeconomica AS (
    SELECT
        -- Chaves Estrangeiras (Granularidade)
        id_municipio,
        ano,
        
        -- Métricas Setoriais
        pib_agropecuaria,
        pib_industria,
        pib_servicos,
        pib_administracao_publica,
        pib_vab_total,
        pib_impostos,
        
        -- Métricas Macro
        pib_total,
        pib_per_capita
    FROM pib
)

SELECT * FROM fato_socioeconomica

{{ config(materialized='table') }}

WITH
dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

pib AS (
    SELECT * FROM {{ ref('pib_municipios') }}
),

fato_socioeconomica AS (
    SELECT
        -- Chave Estrangeira (Dimensão Localidade)
        d.sk_localidade,

        -- Chave Estrangeira (Dimensão Calendário)
        ca.sk_calendario,

        -- Métricas de Valor Adicionado Bruto (VA)
        p.pib_agropecuaria,
        p.pib_industria,
        p.pib_servicos,
        p.pib_administracao_publica,
        p.pib_vab_total,

        -- Impostos e PIB
        p.pib_impostos,
        p.pib_total,
        p.pib_per_capita
    FROM pib p
    INNER JOIN dim_localidade d
        ON p.id_municipio = d.id_municipio
    INNER JOIN dim_calendario ca
        ON p.ano = ca.ano_referencia
)

SELECT * FROM fato_socioeconomica
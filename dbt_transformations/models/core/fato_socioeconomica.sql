{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

pib AS (
    SELECT * FROM {{ ref('stg_pib_municipios') }}
),

fato_com_sk AS (
    SELECT
        -- Chave Estrangeira (Dimensão)
        d.sk_localidade,

        -- Granularidade
        p.ano,

        -- Métricas de Valor Adicionado Bruto (VA) por Setor (conforme IBGE)
        p.pib_agropecuaria AS va_bruto_agropecuaria,
        p.pib_industria AS va_bruto_industria,
        p.pib_servicos AS va_bruto_servicos,
        p.pib_administracao_publica AS va_bruto_administracao_publica,
        p.pib_vab_total AS va_bruto_total,

        -- Impostos líquidos (diferença entre PIB e VAB total)
        p.pib_impostos AS impostos_liquidos,

        -- Produto Interno Bruto Final (PIB = VAB total + Impostos líquidos)
        p.pib_total
    FROM pib p
    INNER JOIN dim_localidade d
        ON p.id_municipio = d.id_municipio
)

SELECT * FROM fato_com_sk

{{ config(materialized='table') }}

WITH
dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

pib AS (
    SELECT * FROM {{ ref('stg_pib_municipios') }}
),

fato_socioeconomica AS (
    SELECT
        -- Chave Estrangeira (Dimensão)
        d.sk_localidade,

        -- Granularidade
        p.ano_competencia AS ano,

        -- Métricas de Valor Adicionado Bruto (VA) por Setor (conforme IBGE)
        p.va_bruto_agropecuaria,
        p.va_bruto_industria,
        p.va_bruto_servicos,
        p.va_bruto_administracao_publica,
        p.va_bruto_total,

        -- Impostos líquidos (diferença entre PIB e VAB total)
        p.impostos_liquidos,

        -- Produto Interno Bruto Final (PIB = VAB total + Impostos líquidos)
        p.pib_total,

        -- PIB per capita (IBGE calcula com população do Censo/estimativas)
        p.pib_per_capita
    FROM pib p
    INNER JOIN dim_localidade d
        ON p.id_municipio = d.id_municipio
)

SELECT * FROM fato_socioeconomica

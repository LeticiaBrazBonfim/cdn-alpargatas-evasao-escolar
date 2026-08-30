WITH source AS (
    SELECT * FROM {{ parquet('pib_municipios') }}
),

pib AS (
    SELECT
        CAST("Código do Município" AS INTEGER) AS id_municipio,
        CAST("Ano" AS INTEGER) AS ano,

        -- Colunas de Valor Adicionado
        CAST("Valor adicionado bruto da Agropecuária, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_agropecuaria,

        CAST("Valor adicionado bruto da Indústria,
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_industria,

        CAST("Valor adicionado bruto dos Serviços,
a preços correntes 
- exceto Administração, defesa, educação e saúde públicas e seguridade social
(R$ 1.000)" AS NUMERIC) AS pib_servicos,

        CAST("Valor adicionado bruto da Administração, defesa, educação e saúde públicas e seguridade social, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_administracao_publica,

        CAST("Valor adicionado bruto total, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_vab_total,

        -- Colunas de Impostos e PIB Final
        CAST("Impostos, líquidos de subsídios, sobre produtos, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_impostos,

        CAST("Produto Interno Bruto, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS pib_total,

        CAST("Produto Interno Bruto per capita, 
a preços correntes
(R$ 1,00)" AS NUMERIC) AS pib_per_capita

    FROM source
    WHERE "Código do Município" IS NOT NULL 
        AND "Ano" IS NOT NULL
    )

SELECT * FROM pib

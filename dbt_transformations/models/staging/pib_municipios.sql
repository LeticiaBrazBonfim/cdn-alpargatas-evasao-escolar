WITH source AS (
    SELECT * FROM {{ source('dev_raw', 'pib_municipios') }}
),

pib_limpo AS (
    SELECT
        CAST("Código do Município" AS INTEGER) AS id_municipio,
        CAST("Ano" AS INTEGER) AS ano_competencia,

        CAST("Valor adicionado bruto da Agropecuária, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS va_bruto_agropecuaria,

        CAST("Valor adicionado bruto da Indústria,
a preços correntes
(R$ 1.000)" AS NUMERIC) AS va_bruto_industria,

        CAST("Valor adicionado bruto dos Serviços,
a preços correntes 
- exceto Administração, defesa, educação e saúde públicas e seguridade social
(R$ 1.000)" AS NUMERIC) AS va_bruto_servicos,

        CAST("Valor adicionado bruto da Administração, defesa, educação e saúde públicas e seguridade social, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS va_bruto_administracao_publica,

        CAST("Valor adicionado bruto total, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS va_bruto_total,

        CAST("Impostos, líquidos de subsídios, sobre produtos, 
a preços correntes
(R$ 1.000)" AS NUMERIC) AS impostos_liquidos,

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

SELECT * FROM pib_limpo
WHERE COALESCE(pib_total, 0) != 0
   OR COALESCE(pib_per_capita, 0) != 0

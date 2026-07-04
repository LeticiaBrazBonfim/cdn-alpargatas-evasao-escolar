WITH source AS (
    SELECT * FROM {{ source('raw', 'projetos_ia') }}
),

clean AS (
    SELECT
        CAST(ano AS INTEGER) AS ano_competencia,
        UPPER(TRIM("ESTADO")) AS sigla_uf,
        UPPER(TRIM("CIDADES")) AS nome_municipio,

        CAST({{ project_metric('Nº de Projetos') }} AS INTEGER) AS projetos_1,
        CAST({{ project_metric('Nº de Projetos.1') }} AS INTEGER) AS projetos_2,
        CAST({{ project_metric('Nº de Projetos.2') }} AS INTEGER) AS projetos_3,
        CAST({{ project_metric('Nº de Projetos.3') }} AS INTEGER) AS projetos_4,
        CAST({{ project_metric('Nº de Projetos.4') }} AS INTEGER) AS projetos_5,
        CAST({{ project_metric('Nº de Projetos.5') }} AS INTEGER) AS projetos_6,

        CAST({{ project_metric('Nº de Beneficiados') }} AS INTEGER) AS beneficiados_1,
        CAST({{ project_metric('Nº de Beneficiados.1') }} AS INTEGER) AS beneficiados_2,
        CAST({{ project_metric('Nº de Beneficiados.2') }} AS INTEGER) AS beneficiados_3,
        CAST({{ project_metric('Nº de Beneficiados.3') }} AS INTEGER) AS beneficiados_4,
        CAST({{ project_metric('Nº de Beneficiados.4') }} AS INTEGER) AS beneficiados_5,
        CAST({{ project_metric('Nº de Beneficiados.5') }} AS INTEGER) AS beneficiados_6

    FROM source
)

SELECT * FROM clean

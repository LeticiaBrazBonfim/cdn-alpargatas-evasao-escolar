WITH source AS (
    SELECT * FROM {{ source('raw', 'projetos_ia') }}
),

-- 1. Importação do dicionário oficial do IBGE
dicionario_ibge AS (
    SELECT 
        id_municipio,
        UPPER(TRIM(nome_municipio)) AS nome_municipio_padrao
        -- Remova completamente a linha que tentava processar a sigla_uf aqui
    FROM {{ ref('stg_dtb') }}
),

-- 2. Limpeza de registros de totais, variações e comentários de planilha
filtro_coluna_cidades AS (
    SELECT *
    FROM source
    WHERE 
        "CIDADES" IS NOT NULL 
        AND "ESTADO" IS NOT NULL -- Elimina as anotações textuais soltas que não têm Estado preenchido
        AND TRIM("ESTADO") != ''
        AND UPPER(TRIM("CIDADES")) NOT LIKE 'TOTAL%'
        AND UPPER(TRIM("CIDADES")) NOT LIKE 'VARIAÇÃO%'
        AND UPPER(TRIM("CIDADES")) NOT LIKE 'OBS.%'
),

-- 3. Pivotamento, tipagem e padronização ortográfica
transformacao AS (
    SELECT
        CAST(ano AS INTEGER) AS ano_competencia,
        UPPER(TRIM("ESTADO")) AS sigla_uf,
        
        -- Dicionário de Correção (Data Cleansing) para as cidades poluídas
        CASE 
            WHEN UPPER(TRIM("CIDADES")) = 'CAMPINA GRANDE- MIXING CENTER' THEN 'CAMPINA GRANDE'
            WHEN UPPER(TRIM("CIDADES")) = 'QUEIMADAS *' THEN 'QUEIMADAS'
            ELSE UPPER(TRIM("CIDADES"))
        END AS nome_municipio,
        
        (
            COALESCE(CAST({{ project_metric('Nº de Projetos') }} AS INTEGER), 0)
            {% for i in range(1, 6) %}
            + COALESCE(CAST({{ project_metric('Nº de Projetos.' ~ i) }} AS INTEGER), 0)
            {% endfor %}
        ) AS total_projetos_ia,

        (
            COALESCE(CAST({{ project_metric('Nº de Beneficiados') }} AS INTEGER), 0)
            {% for i in range(1, 6) %}
            + COALESCE(CAST({{ project_metric('Nº de Beneficiados.' ~ i) }} AS INTEGER), 0)
            {% endfor %}
        ) AS total_beneficiados
    FROM filtro_coluna_cidades
)

-- 4. Projeção final
SELECT 
    ibge.id_municipio,
    t.ano_competencia,
    t.total_projetos_ia,
    t.total_beneficiados,
    t.sigla_uf,
    t.nome_municipio 
FROM transformacao t
LEFT JOIN dicionario_ibge ibge
    ON t.nome_municipio = ibge.nome_municipio_padrao
    -- Remova completamente o operador AND t.sigla_uf = ibge.sigla_uf

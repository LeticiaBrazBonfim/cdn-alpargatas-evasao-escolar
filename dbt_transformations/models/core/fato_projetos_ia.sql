{{ config(materialized='table') }}

WITH

dim_calendario AS (
    SELECT * FROM {{ ref('dim_calendario') }}
),

dim_localidade AS (
    SELECT * FROM {{ ref('dim_localidade') }}
),

stg_projetos AS (
    SELECT * FROM {{ ref('projetos_ia') }}
),

uf_mapping AS (
    SELECT *
    FROM (
        VALUES
            ('AC', 'ACRE'), ('AL', 'ALAGOAS'), ('AP', 'AMAPÁ'), ('AM', 'AMAZONAS'),
            ('BA', 'BAHIA'), ('CE', 'CEARÁ'), ('DF', 'DISTRITO FEDERAL'),
            ('ES', 'ESPÍRITO SANTO'), ('GO', 'GOIÁS'), ('MA', 'MARANHÃO'),
            ('MT', 'MATO GROSSO'), ('MS', 'MATO GROSSO DO SUL'), ('MG', 'MINAS GERAIS'),
            ('PA', 'PARÁ'), ('PB', 'PARAÍBA'), ('PR', 'PARANÁ'), ('PE', 'PERNAMBUCO'),
            ('PI', 'PIAUÍ'), ('RJ', 'RIO DE JANEIRO'), ('RN', 'RIO GRANDE DO NORTE'),
            ('RS', 'RIO GRANDE DO SUL'), ('RO', 'RONDÔNIA'), ('RR', 'RORAIMA'),
            ('SC', 'SANTA CATARINA'), ('SP', 'SÃO PAULO'), ('SE', 'SERGIPE'),
            ('TO', 'TOCANTINS')
    ) AS t(sigla, nome_completo)
),

clean AS (
    SELECT
        p.ano_competencia,
        p.sigla_uf,

        CASE
            WHEN p.nome_municipio = 'CAMPINA GRANDE- MIXING CENTER' THEN 'CAMPINA GRANDE'
            WHEN p.nome_municipio = 'QUEIMADAS *' THEN 'QUEIMADAS'
            ELSE p.nome_municipio
        END AS nome_municipio,

        COALESCE(p.projetos_1, 0) + COALESCE(p.projetos_2, 0)
        + COALESCE(p.projetos_3, 0) + COALESCE(p.projetos_4, 0)
        + COALESCE(p.projetos_5, 0) + COALESCE(p.projetos_6, 0) AS quantidade_projetos,

        COALESCE(p.beneficiados_1, 0) + COALESCE(p.beneficiados_2, 0)
        + COALESCE(p.beneficiados_3, 0) + COALESCE(p.beneficiados_4, 0)
        + COALESCE(p.beneficiados_5, 0) + COALESCE(p.beneficiados_6, 0) AS quantidade_beneficiados

    FROM stg_projetos p
),

com_uf AS (
    SELECT
        c.ano_competencia,
        c.quantidade_projetos,
        c.quantidade_beneficiados,
        c.nome_municipio,
        u.nome_completo AS nome_uf
    FROM clean c
    LEFT JOIN uf_mapping u
        ON c.sigla_uf = u.sigla
)

SELECT
    d.sk_localidade,
    ca.sk_calendario,
    c.quantidade_projetos,
    c.quantidade_beneficiados
FROM com_uf c
INNER JOIN dim_localidade d
    ON c.nome_municipio = d.nome_municipio
    AND c.nome_uf = d.nome_uf
INNER JOIN dim_calendario ca
    ON c.ano_competencia = ca.ano_referencia
WHERE COALESCE(c.quantidade_projetos, 0) != 0
   OR COALESCE(c.quantidade_beneficiados, 0) != 0
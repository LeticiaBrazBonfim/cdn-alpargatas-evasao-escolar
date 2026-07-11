# Dashboard Estratégico — Instituto Alpargatas

Análise de dados educacionais e socioeconômicos para otimizar o impacto social e combater a evasão escolar nos municípios de atuação do Instituto Alpargatas.

[Documentação Técnica](dbt_transformations/GUIA_INTERNO.md)

---

## Contexto

Este projeto integra dados públicos (INEP, IBGE) com dados privados do Instituto Alpargatas em um **modelo dimensional Kimball (Star Schema)** implementado em **dbt (Postgres/Neon)**. O objetivo é oferecer insights baseados em evidências através de dashboards no Metabase.

---

## Fontes de Dados

### Públicas
- **INEP** — Índice de Desenvolvimento da Educação Básica (IDEB) 2005-2023, Taxa de Distorção Idade-Série 2019-2023
- **IBGE** — Produto Interno Bruto (PIB) Municipal 2010-2021, Diretório Territorial Brasileiro (DTB)

### Privadas
- **Instituto Alpargatas** — Projetos de Inteligência Artificial Educacional e beneficiários (2020-2025)

---

## Arquitetura

O projeto adota o paradigma ELT (Extract, Load, Transform), centralizando o processamento computacional no motor do banco de dados em nuvem.

```
data/raw/*.parquet
    │
    ▼  Ingestão via load_raw_to_postgres.py (DuckDB atua apenas como leitor)
    │
┌────────────────────────────────────────────────────────┐
│                    Neon (PostgreSQL)                   │
│                                                        │
│  [schema: raw]       (Tabelas brutas em formato TEXT)  │
│    │                                                   │
│    ▼ dbt run         (Transformação e Casting)         │
│  [schema: staging]   (Views espelhadas 1:1)            │
│    │                                                   │
│    ▼ dbt run         (Materialização Física)           │
│  [schema: core]      (Tabelas do Modelo Dimensional)   │
└──────────────────────────┬─────────────────────────────┘
                           │
                           ▼ Consultas SQL via conexão direta
                        Metabase
                      (Dashboards)
```

### Staging (5 modelos, `materialized='view'`)

| Modelo | Fonte | Função |
|--------|-------|--------|
| `stg_dtb` | raw.dtb_municipios | Limpeza + UPPER/TRIM de nomes |
| `stg_pib_municipios` | raw.pib_municipios | REPLACE pt-BR → US, CAST NUMERIC |
| `stg_projetos_ia` | raw.projetos_ia | 1:1, 12 colunas (projetos_1..6 + beneficiados_1..6) |
| `stg_ideb` | raw.ideb_municipios | Wide format, Jinja gera 100+ colunas |
| `stg_taxa_distorcao` | raw.taxa_distorcao | Safe_cast de taxas (trata '--' como NULL) |

### Core (2 dimensões + 5 fatos, `materialized='table'`)

**Dimensões:**
- `dim_localidade` (5.571 municípios) — SK = MD5(id_municipio)
- `dim_rede` (6 redes) — SK = MD5(nome_rede), redes: ESTADUAL, MUNICIPAL, FEDERAL, PRIVADA, TOTAL, DESCONHECIDO

**Fatos:**

| Fato | Granularidade | Linhas | Métricas |
|------|---------------|--------|----------|
| `fato_ideb` | município + rede + ano | 82.726 | IDEB observado/projeção, notas SAEB, taxas aprovação, indicador rendimento |
| `fato_projetos_ia` | município + ano | 100 | Quantidade projetos, quantidade beneficiados |
| `fato_socioeconomica` | município + ano | 66.825 | PIB, VAB por setor, impostos líquidos |
| `fato_taxa_distorcao_municipio` | município + ano | 27.850 | Taxa distorção ensino fundamental/médio |
| `fato_taxa_distorcao_rede_categoria` | município + ano + categoria + rede | 151.146 | Taxa distorção ensino fundamental/médio |

---

## Qualidade e Testes

**46 testes automáticos** validam o pipeline:

| Tipo | Qtd | O que valida |
|------|-----|--------------|
| `unique` | 5 | SKs, chaves naturais |
| `not_null` | 27 | Colunas obrigatórias |
| `relationships` | 10 | Integridade referencial (FK → PK) |
| Singulares | 3 | Chaves compostas (staging) |

---

## Repositório

```
├── README.md                              # Este arquivo
├── AGENTS.md                              # Diretrizes do assistente OpenCode
├── data/raw/                              # Arquivos .parquet brutos
├── dbt_transformations/
│   ├── GUIA_INTERNO.md                    # ⬅ Documentação técnica completa
│   ├── dbt_project.yml                    # Configuração dbt
│   ├── models/
│   │   ├── sources.yml                    # Fontes raw
│   │   ├── staging/                       # 5 modelos staging (views)
│   │   ├── core/                          # 7 modelos core (tables)
│   │   └── staging/stg_schema.yml         # Testes staging
│   ├── macros/safe_cast.sql               # Macros de casting seguro
│   ├── scripts/load_raw_to_postgres.py    # Carga parquet → Neon
│   └── tests/                             # Testes singulares
└── requirements.txt                       # dbt-postgres, duckdb
```

---

## Licença

Projeto acadêmico e laboratório pessoal — **Leticia Braz Bonfim**.

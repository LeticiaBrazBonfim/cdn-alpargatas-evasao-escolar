# Guia Interno — Pipeline dbt

## Índice
1. [Visão Geral do Fluxo](#visão-geral-do-fluxo)
2. [Pré-requisitos](#pré-requisitos)
3. [Setup Inicial](#setup-inicial)
4. [Comandos de Execução](#comandos-de-execução)
5. [Modelos Detalhados](#modelos-detalhados)
6. [Testes e Validação](#testes-e-validação)
7. [Troubleshooting](#troubleshooting)

---

## Visão Geral do Fluxo

Pipeline ELT com 3 camadas:

```
data/raw/*.parquet

↓  load_raw_to_postgres.py (DuckDB → Neon)
dev_raw.dbt_municipios, dev_raw.pib_municipios, dev_raw.projetos_ia,
dev_raw.ideb_municipios, dev_raw.taxa_distorcao

↓  dbt run
dbt_municipios, ideb_municipios, pib_municipios, projetos_ia, taxa_distorcao  (views, 1:1)

↓  dbt run
dim_calendario → fato_ideb_municipios, fato_projetos_ia, fato_pib_municipios, fato_taxa_distorcao_municipio, fato_taxa_distorcao_rede_categoria
dim_localidade → fato_ideb_municipios, fato_projetos_ia, fato_pib_municipios, fato_taxa_distorcao_municipio, fato_taxa_distorcao_rede_categoria
dim_rede → fato_ideb_municipios, fato_taxa_distorcao_rede_categoria
    ↓  dbt test
54 testes de integridade

↓  Metabase
Dashboards analíticos
```

**Ordem de execução padrão:**
1. `python scripts/load_raw_to_postgres.py --target dev --if-exists replace` (1x ou quando os parquets mudarem)
2. `dbt run --target dev`
3. `dbt test --target dev`

---

## Pré-requisitos

- **Python 3.10+** com `pip install -r requirements.txt` (dbt-postgres, duckdb)
- **Neon** (Postgres) com schemas `dev_raw`, `dev_stg`, `dev_core` criados
- **`~/.dbt/profiles.yml`** com credenciais:

```yaml
alpargatas-impacto-educacional:
  outputs:
    dev:
      type: postgres
      host: [seu-host-neon]
      user: [seu-usuario]
      password: [sua-senha]
      port: 5432
      dbname: neondb
      schema: dev_core
      threads: 4
      sslmode: require
    prod:
      type: postgres
      host: [seu-host-neon]
      user: [seu-usuario]
      password: [sua-senha]
      port: 5432
      dbname: neondb
      schema: public
      threads: 4
      sslmode: require
  target: dev
```

> **Nota:** O `schema` do target `dev` aponta para `dev_core` (schema de destino dos modelos core). Os modelos staging materializam em `dev_stg` via `+schema: stg` no dbt_project.yml. O script Python carrega direto em `dev_raw`.

---

## Setup Inicial

```bash
cd dbt_transformations
pip install -r requirements.txt
dbt debug              # Verificar conexão
```

---

## Comandos de Execução

### Carga dos dados brutos (1x ou quando parquets forem atualizados)

```bash
python scripts/load_raw_to_postgres.py --target dev --if-exists replace
```

**Flags:**
| Flag | Função |
|------|--------|
| `--target dev` | Usa credenciais do target `dev` no profiles.yml |
| `--if-exists replace` | Recria as tabelas raw (DROP + CREATE) |
| `--if-exists skip` | Mantém tabelas existentes |
| `--if-exists fail` | Erro se tabela já existir (padrão) |

**O script faz:** Lê todos os `.parquet` de `data/raw/` via DuckDB, cria tabelas no Neon com **todas as colunas como TEXT** (preservação bruta), usa `COPY` para bulk load. O mapeamento de nomes: `dtb_municipios.parquet` → `dbt_municipios`.

**Verificar:**
```sql
SELECT COUNT(*) FROM dev_raw.dbt_municipios;       -- 5571
SELECT COUNT(*) FROM dev_raw.pib_municipios;        -- 66825
SELECT COUNT(*) FROM dev_raw.projetos_ia;           -- 135
SELECT COUNT(*) FROM dev_raw.ideb_municipios;       -- ~1430
SELECT COUNT(*) FROM dev_raw.taxa_distorcao;        -- ~327944
```

### dbt parse (validar sintaxe sem executar)

```bash
dbt parse --target dev
```

### dbt run (executar transformações)

```bash
## Completo (todos os modelos)
dbt run --target dev

# Modelo específico
dbt run --select fato_ideb_municipios --target dev

# Modelo + dependentes
dbt run --select +dim_localidade --target dev

# Apenas staging
dbt run --select tag:staging --target dev

# Apenas core
dbt run --select tag:core --target dev
```

### dbt test (validar integridade)

```bash
# Completo (54 testes)
dbt test --target dev

# Modelo específico
dbt test --select dim_localidade --target dev

# Apenas relações
dbt test --select tag:relationships --target dev

# Apenas singulares (chaves compostas)
dbt test --select test_type:singular --target dev
```

### dbt docs (documentação interativa)

```bash
dbt docs generate --target dev
dbt docs serve               # http://localhost:8080
```

---

## Modelos Detalhados

### Staging (5 views — 1:1 com raw, sem regras de negócio)

#### `dbt_municipios`
- **Fonte**: `dev_raw.dbt_municipios`
- **Transformações**: CAST ids para INTEGER, UPPER(TRIM) em nomes
- **Colunas**: id_municipio, nome_municipio, id_uf, nome_uf, id_regiao_geografica_imediata, nome_regiao_geografica_imediata
- **Testes**: `unique` + `not_null` em id_municipio
- **Linhas**: 5.571

#### `pib_municipios`
- **Fonte**: `dev_raw.pib_municipios`
- **Transformações**: CAST ids/ano para INTEGER, CAST NUMERIC direto nos valores monetários (dados já em formato US no Neon)
- **Colunas**: id_municipio, ano_competencia, va_bruto_*, impostos_liquidos, pib_total, pib_per_capita
- **Testes**: `not_null` em id_municipio + ano_competencia, `relationships` → dbt_municipios
- **Singular**: unique_combination_pib_municipios (id_municipio, ano_competencia)
- **Linhas**: 66.825

#### `projetos_ia`
- **Fonte**: `dev_raw.projetos_ia`
- **Transformações**: CAST para INTEGER nas 12 colunas métricas, nomes em snake_case
- **Colunas**: ano_competencia, sigla_uf, nome_municipio, projetos_1..6, beneficiados_1..6
- **Observação**: JOIN com dbt_municipios NÃO é feito aqui (seria violação 1:1). O lookup é feito no fato.
- **Testes**: `not_null` em ano_competencia
- **Linhas**: 135

#### `ideb_municipios`
- **Fonte**: `dev_raw.ideb_municipios`
- **Transformações**: Wide format (100+ colunas de métricas por ano), safe_cast_numeric_column com '-', Jinja gera colunas para 10 anos (2005-2023)
- **Colunas**: id_municipio, nome_municipio, sigla_uf, nome_rede, vl_observado_2005..vl_indicador_rend_2023
- **Testes**: `not_null` + `relationships` em id_municipio → dbt_municipios
- **Singular**: unique_combination_ideb_municipios (id_municipio, nome_rede)
- **Linhas**: ~1.430

#### `taxa_distorcao`
- **Fonte**: `dev_raw.taxa_distorcao`
- **Transformações**: safe_cast_numeric_column com '--', UPPER em categorias, divisão por 100.0 (decimal)
- **Colunas**: id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa, taxa_distorcao_*
- **Testes**: `not_null` em id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa; `relationships` → dbt_municipios
- **Singular**: unique_combination_taxa_distorcao (id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa)
- **Linhas**: 327.934

---

### Core (8 tabelas — modelo dimensional Kimball)

#### `dim_localidade`
- **Tipo**: Dimensão (Type 1)
- **SK**: `MD5(CAST(id_municipio AS VARCHAR))` — hash imutável e idempotente
- **Granularidade**: 1 linha por município
- **Fonte**: `dbt_municipios` com `SELECT DISTINCT`
- **Atributos**: nome_municipio, id_uf, nome_uf, id_regiao_geografica_imediata, nome_regiao_geografica_imediata; colunas compostas `id_nome_*` via CONCAT
- **Testes**: `unique` + `not_null` em sk_localidade e id_municipio
- **Linhas**: 5.571

#### `dim_rede`
- **Tipo**: Dimensão (Type 1) — Conformed Dimension
- **SK**: `MD5(nome_rede)` — hash imutável
- **Granularidade**: 1 linha por rede
- **Fonte**: `ideb_municipios` (coluna REDE) e `taxa_distorcao` (coluna NO_DEPENDENCIA) — INEP
- **Granularidade**: 1 linha por rede
- **Redes**: ESTADUAL (id=2), MUNICIPAL (id=4), FEDERAL (id=6), PRIVADA (id=8), TOTAL (agregado). DESCONHECIDO (fallback p/ chaves órfãs).
- **Atributos**: nome_rede, id_rede (2, 4, 6, 8), id_nome_rede (CASE WHEN id_rede NOT NULL THEN CONCAT ELSE nome_rede)
- **Testes**: `unique` em sk_rede e id_rede (id_rede é NULL para TOTAL e DESCONHECIDO)
- **Linhas**: 6

#### `dim_calendario`
- **Tipo**: Dimensão (Type 1)
- **SK**: `MD5(CAST(ano_referencia AS VARCHAR))` — hash imutável
- **Granularidade**: 1 linha por ano
- **Fonte**: CTE recursiva gerando anos de 2000 a 2031
- **Atributos**: ano_referencia
- **Testes**: `unique` + `not_null` em sk_calendario; `not_null` em ano_referencia
- **Linhas**: 32

#### `fato_ideb_municipios`
- **Granularidade**: município + rede + ano
- **Fonte**: `ideb_municipios` (UNPIVOT via Jinja `{% for ano in anos %} UNION ALL`)
- **Regras de negócio** (na CTE `unpivot`):
  - `ROUND(vl_nota_*, 2)` nas notas SAEB
  - `/ 100.0` nas taxas de aprovação
  - `ideb_projecao` apenas para anos 2007-2021 (CAST NULL para demais)
- **Filtro**: WHERE com 13 condições OR metric IS NOT NULL (elimina linhas totalmente vazias)
- **JOINs**: dim_rede (6 linhas) primeiro, dim_localidade (5.571) segundo, dim_calendario (32) terceiro — otimizado por cardinalidade
- **Testes**: `not_null` em sk_localidade, sk_rede, sk_calendario; `relationships` → dim_localidade, dim_rede e dim_calendario
- **Linhas**: 82.726

#### `fato_projetos_ia`
- **Granularidade**: município + ano
- **Fonte**: `projetos_ia`
- **Regras de negócio** (na CTE `clean`):
  - CASE WHEN para corrigir nomes: 'CAMPINA GRANDE- MIXING CENTER' → 'CAMPINA GRANDE', 'QUEIMADAS *' → 'QUEIMADAS'
  - COALESCE em cada coluna `projetos_N` + soma (6 colunas → 1 métrica)
  - COALESCE em cada coluna `beneficiados_N` + soma (6 colunas → 1 métrica)
- **Lookup**: CTE `uf_mapping` (VALUES com 27 UFs sigla→nome_completo) resolve sigla_uf → nome_uf para JOIN
- **JOIN**: `nome_municipio + nome_uf` (duas condições) previne cartesiano entre cidades homônimas; `ano_competencia` → `dim_calendario.ano_referencia`
- **Testes**: `not_null` em sk_localidade, sk_calendario, quantidade_projetos, quantidade_beneficiados; `relationships` → dim_localidade e dim_calendario
- **Linhas**: 90

#### `fato_pib_municipios`
- **Granularidade**: município + ano
- **Fonte**: `pib_municipios`
- **JOIN**: `id_municipio` → `dim_localidade`; `ano_competencia` → `dim_calendario.ano_referencia`
- **Testes**: `not_null` em sk_localidade, sk_calendario; `relationships` → dim_localidade e dim_calendario
- **Linhas**: 66.825

#### `fato_taxa_distorcao_municipio`
- **Granularidade**: município + ano (grão macro — agregado municipal)
- **Fonte**: `taxa_distorcao` WHERE `categoria_localidade = 'TOTAL' AND dependencia_administrativa = 'TOTAL'`
- **JOIN**: `id_municipio` → `dim_localidade`; `ano_competencia` → `dim_calendario.ano_referencia`
- **Testes**: `not_null` em sk_localidade, sk_calendario; `relationships` → dim_localidade e dim_calendario
- **Observação**: TDI armazenada como decimal (0.5 = 50%). A divisão por 100.0 ocorre na staging (`taxa_distorcao`).
- **Linhas**: 27.848

#### `fato_taxa_distorcao_rede_categoria`
- **Granularidade**: município + ano + categoria_localidade + rede (grão micro — desagregado)
- **Fonte**: `taxa_distorcao` WHERE `categoria_localidade != 'TOTAL' OR dependencia_administrativa != 'TOTAL'`
- **JOIN**: `id_municipio` → `dim_localidade`; `ano_competencia` → `dim_calendario.ano_referencia`; `dependencia_administrativa` → `dim_rede.nome_rede`
  - `COALESCE(sk_rede, MD5('DESCONHECIDO'))` p/ preservar integridade referencial
- **Testes**: `not_null` em sk_localidade, sk_rede, sk_calendario; `relationships` → dim_localidade, dim_rede e dim_calendario
- **Observação**: TDI armazenada como decimal (0.5 = 50%). A divisão por 100.0 ocorre na staging (`taxa_distorcao`).
- **Linhas**: 292.318

---

## Testes e Validação

### 54 testes distribuídos:

| Tipo | Qtd | O que testa |
|------|-----|-------------|
| `not_null` | 30 | Colunas obrigatórias em staging + dimensões + fatos |
| `unique` | 6 | SKs (sk_localidade, sk_rede, sk_calendario) e NKs (id_municipio, id_rede) |
| `relationships` | 15 | FKs nos fatos → dimensões; FKs staging → dbt_municipios |
| Singulares (SQL) | 3 | Chaves compostas: (id_municipio, ano) no PIB; (id_municipio, nome_rede) no IDEB; (4 colunas) na taxa_distorcao |

### Testes por modelo:

**Staging:**
| Modelo | not_null | unique | relationships | singular |
|--------|----------|--------|---------------|----------|
| dbt_municipios | id_municipio | id_municipio | — | — |
| pib_municipios | id_municipio, ano_competencia | — | → dbt_municipios | unique_combination |
| projetos_ia | ano_competencia | — | — | — |
| ideb_municipios | id_municipio | — | → dbt_municipios | unique_combination |
| taxa_distorcao | id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa | — | → dbt_municipios | unique_combination |

**Core:**
| Modelo | not_null | unique | relationships |
|--------|----------|--------|---------------|
| dim_localidade | sk_localidade, id_municipio, id_uf | sk_localidade, id_municipio | — |
| dim_rede | sk_rede | sk_rede, id_rede | — |
| dim_calendario | sk_calendario, ano_referencia | sk_calendario | — |
| fato_ideb_municipios | sk_localidade, sk_rede, sk_calendario | — | → dim_localidade, dim_rede, dim_calendario |
| fato_projetos_ia | sk_localidade, sk_calendario, quantidade_projetos, quantidade_beneficiados | — | → dim_localidade, dim_calendario |
| fato_pib_municipios | sk_localidade, sk_calendario | — | → dim_localidade, dim_calendario |
| fato_taxa_distorcao_municipio | sk_localidade, sk_calendario | — | → dim_localidade, dim_calendario |
| fato_taxa_distorcao_rede_categoria | sk_localidade, sk_rede, sk_calendario | — | → dim_localidade, dim_rede, dim_calendario |

### Diagnóstico de falhas

**`not_null_stg_projetos_ia_nome_municipio` FAIL:**
- Causa: raw.projetos_ia tem NULLs legítimos em nome_municipio
- Ação: Remover `not_null` do schema.yml (staging é 1:1)

**`relationships_fato_projetos_ia_sk_localidade` FAIL:**
- Causa: SK no fato não encontrada na dimensão (nome_municipio + nome_uf sem match)
- Ação: Verificar CASE WHEN de limpeza ou uf_mapping

**`unique_dim_localidade_sk_localidade` FAIL:**
- Causa: MD5 collision ou DISTINCT mal aplicado
- Ação: Verificar se há id_municipio duplicado em dbt_municipios

---

## Troubleshooting

### `dbt debug` falha
```bash
cat ~/.dbt/profiles.yml
# Verificar host, user, password, sslmode: require
```

### `dbt run` falha em um modelo
```bash
dbt run --select dbt_municipios -vv        # Verboso, mostra SQL compilado
# Verificar target/compiled/ para o SQL exato
```

### Teste de integridade referencial falha
```sql
-- Encontrar chaves órfãs
SELECT f.sk_localidade
FROM dev_core.fato_projetos_ia f
LEFT JOIN dev_core.dim_localidade d ON d.sk_localidade = f.sk_localidade
WHERE d.sk_localidade IS NULL;
```

### Limpar e recriar tudo
```bash
# Dropa todas as tabelas/views e recria
dbt run --full-refresh --target dev
```

---

## Macros

### `safe_cast_numeric(string_value)` — macro raiz
Valida string com regex antes de CAST:
```sql
regexp '^[+-]?([0-9]+([.][0-9]*)?|[.][0-9]+)$'
```
Retorna NULL se inválido.

### `safe_cast_numeric_column(col, null_val)` — macro de staging
Orquestra `adapter.quote()` + `NULLIF` para caracteres de ausência ('--', '-').

### `project_metric(col)` — macro específica projetos
Remove sufixo `.0` via `regexp_replace` antes do safe_cast.

---

## Targets

| Target | Schema | Uso |
|--------|--------|-----|
| `dev` | `dev_core` | Desenvolvimento, testes |
| `prod` | `public` | Produção, dashboards Metabase |

```bash
dbt run --target prod     # Cria em schema public
dbt test --target prod    # Testa produção
```
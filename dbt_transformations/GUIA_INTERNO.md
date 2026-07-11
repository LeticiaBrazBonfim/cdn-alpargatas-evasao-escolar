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
raw.dtb_municipios, raw.pib_municipios, raw.projetos_ia,
raw.ideb_municipios, raw.taxa_distorcao

↓  dbt run
stg_dtb, stg_pib_municipios, stg_projetos_ia, stg_ideb, stg_taxa_distorcao  (views, 1:1)

↓  dbt run
dim_localidade → fato_ideb, fato_projetos_ia, fato_socioeconomica, fato_taxa_distorcao_municipio, fato_taxa_distorcao_rede_categoria
dim_rede

↓  dbt test
46 testes de integridade

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
- **Neon** (Postgres) com schema `dev` configurado
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
      schema: dev
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
| `--schema raw` | Schema de destino (padrão: schema do target) |

**O script faz:** Lê todos os `.parquet` de `data/raw/` via DuckDB, cria tabelas no Neon com **todas as colunas como TEXT** (preservação bruta), usa `COPY` para bulk load.

**Verificar:**
```sql
SELECT COUNT(*) FROM raw.dtb_municipios;       -- 5571
SELECT COUNT(*) FROM raw.pib_municipios;        -- 66825
SELECT COUNT(*) FROM raw.projetos_ia;           -- 135
SELECT COUNT(*) FROM raw.ideb_municipios;       -- ~1430
SELECT COUNT(*) FROM raw.taxa_distorcao;        -- ~327944
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
dbt run --select fato_ideb --target dev

# Modelo + dependentes
dbt run --select +dim_localidade --target dev

# Apenas staging
dbt run --select tag:staging --target dev

# Apenas core
dbt run --select tag:core --target dev
```

### dbt test (validar integridade)

```bash
# Completo (46 testes)
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

#### `stg_dtb`
- **Fonte**: `raw.dtb_municipios`
- **Transformações**: CAST ids para INTEGER, UPPER(TRIM) em nomes
- **Colunas**: id_municipio, nome_municipio, id_uf, nome_uf, id_regiao_geografica_imediata, nome_regiao_geografica_imediata
- **Testes**: `unique` + `not_null` em id_municipio
- **Linhas**: 5.571

#### `stg_pib_municipios`
- **Fonte**: `raw.pib_municipios`
- **Transformações**: CAST ids/ano para INTEGER, REPLACE aninhadas (pt-BR → US) + CAST NUMERIC nos valores monetários
- **Colunas**: id_municipio, ano_competencia, va_bruto_*, impostos_liquidos, pib_total, pib_per_capita
- **Testes**: `not_null` em id_municipio + ano_competencia, `relationships` → stg_dtb
- **Singular**: unique_combination_stg_pib_municipios (id_municipio, ano_competencia)
- **Linhas**: 66.825

#### `stg_projetos_ia`
- **Fonte**: `raw.projetos_ia`
- **Transformações**: CAST para INTEGER nas 12 colunas métricas, nomes em snake_case
- **Colunas**: ano_competencia, sigla_uf, nome_municipio, projetos_1..6, beneficiados_1..6
- **Observação**: JOIN com stg_dtb NÃO é feito aqui (seria violação 1:1). O lookup é feito no fato.
- **Testes**: `not_null` em ano_competencia
- **Linhas**: 135

#### `stg_ideb`
- **Fonte**: `raw.ideb_municipios`
- **Transformações**: Wide format (100+ colunas de métricas por ano), safe_cast_numeric_column com '-', Jinja gera colunas para 10 anos (2005-2023)
- **Colunas**: id_municipio, nome_municipio, sigla_uf, nome_rede, vl_observado_2005..vl_indicador_rend_2023
- **Testes**: `not_null` + `relationships` em id_municipio → stg_dtb
- **Singular**: unique_combination_stg_ideb (id_municipio, nome_rede)
- **Linhas**: ~1.430

#### `stg_taxa_distorcao`
- **Fonte**: `raw.taxa_distorcao`
- **Transformações**: safe_cast_numeric_column com '--', UPPER em categorias
- **Colunas**: id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa, taxa_distorcao_*
- **Testes**: `not_null` em id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa; `relationships` → stg_dtb
- **Singular**: unique_combination_stg_taxa_distorcao (id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa)
- **Linhas**: 327.934

---

### Core (7 tabelas — modelo dimensional Kimball)

#### `dim_localidade`
- **Tipo**: Dimensão (Type 1)
- **SK**: `MD5(CAST(id_municipio AS VARCHAR))` — hash imutável e idempotente
- **Granularidade**: 1 linha por município
- **Fonte**: `stg_dtb` com `SELECT DISTINCT`
- **Atributos**: nome_municipio, id_uf, nome_uf, id_regiao_geografica_imediata, nome_regiao_geografica_imediata; colunas compostas `id_nome_*` via CONCAT
- **Testes**: `unique` + `not_null` em sk_localidade e id_municipio
- **Linhas**: 5.571

#### `dim_rede`
- **Tipo**: Dimensão (Type 1) — Conformed Dimension
- **SK**: `MD5(nome_rede)` — hash imutável
- **Granularidade**: 1 linha por rede (6 registros)
- **Fonte**: `stg_ideb.nome_rede` UNION `stg_taxa_distorcao.dependencia_administrativa`; whitelist: ESTADUAL, MUNICIPAL, FEDERAL, PRIVADA, TOTAL; fallback DESCONHECIDO
- **Atributos**: nome_rede, id_rede (2, 4, 6, 8), id_nome_rede (CASE WHEN id_rede NOT NULL THEN CONCAT ELSE nome_rede)
- **Testes**: `unique` em sk_rede e id_rede (id_rede é NULL para TOTAL e DESCONHECIDO)
- **Linhas**: 6

#### `fato_ideb`
- **Granularidade**: município + rede + ano
- **Fonte**: `stg_ideb` (UNPIVOT via Jinja `{% for ano in anos %} UNION ALL`)
- **Regras de negócio** (na CTE `unpivot`):
  - `ROUND(vl_nota_*, 2)` nas notas SAEB
  - `/ 100.0` nas taxas de aprovação
  - `ideb_projecao` apenas para anos 2007-2021 (CAST NULL para demais)
- **Filtro**: WHERE com 13 condições OR metric IS NOT NULL (elimina linhas totalmente vazias)
- **JOINs**: dim_rede (6 linhas) primeiro, dim_localidade (5.571) segundo — otimizado por cardinalidade
- **Testes**: `not_null` em sk_localidade, sk_rede, ano; `relationships` → dim_localidade e dim_rede
- **Linhas**: 82.726

#### `fato_projetos_ia`
- **Granularidade**: município + ano
- **Fonte**: `stg_projetos_ia`
- **Regras de negócio** (na CTE `clean`):
  - CASE WHEN para corrigir nomes: 'CAMPINA GRANDE- MIXING CENTER' → 'CAMPINA GRANDE', 'QUEIMADAS *' → 'QUEIMADAS'
  - COALESCE em cada coluna `projetos_N` + soma (6 colunas → 1 métrica)
  - COALESCE em cada coluna `beneficiados_N` + soma (6 colunas → 1 métrica)
- **Lookup**: CTE `uf_mapping` (VALUES com 27 UFs sigla→nome_completo) resolve sigla_uf → nome_uf para JOIN
- **JOIN**: `nome_municipio + nome_uf` (duas condições) previne cartesiano entre cidades homônimas
- **Testes**: `not_null` em sk_localidade, ano, quantidade_projetos, quantidade_beneficiados; `relationships` → dim_localidade
- **Linhas**: 100

#### `fato_socioeconomica`
- **Granularidade**: município + ano
- **Fonte**: `stg_pib_municipios`
- **JOIN**: `id_municipio` (numérico)
- **Testes**: `not_null` em sk_localidade, ano; `relationships` → dim_localidade
- **Linhas**: 66.825

#### `fato_taxa_distorcao_municipio`
- **Granularidade**: município + ano (grão macro — agregado municipal)
- **Fonte**: `stg_taxa_distorcao` WHERE `categoria_localidade = 'TOTAL' AND dependencia_administrativa = 'TOTAL'`
- **JOIN**: `id_municipio` → `dim_localidade`
- **Testes**: `not_null` em sk_localidade, ano; `relationships` → dim_localidade
- **Linhas**: 27.850

#### `fato_taxa_distorcao_rede_categoria`
- **Granularidade**: município + ano + categoria_localidade + rede (grão micro — desagregado)
- **Fonte**: `stg_taxa_distorcao` WHERE `categoria_localidade != 'TOTAL' AND dependencia_administrativa != 'TOTAL'`
- **JOIN**: `id_municipio` → `dim_localidade`; `dependencia_administrativa` → `dim_rede.nome_rede`
  - `COALESCE(sk_rede, MD5('DESCONHECIDO'))` p/ preservar integridade referencial
- **Testes**: `not_null` em sk_localidade, sk_rede, ano; `relationships` → dim_localidade e dim_rede
- **Linhas**: 151.146

---

## Testes e Validação

### 46 testes distribuídos:

| Tipo | Qtd | O que testa |
|------|-----|-------------|
| `not_null` | 27 | Colunas obrigatórias em staging + dimensões + fatos |
| `unique` | 5 | SKs (sk_localidade, sk_rede) e NKs (id_municipio, id_rede) |
| `relationships` | 10 | FKs nos fatos → dimensões; FKs staging → stg_dtb |
| Singulares (SQL) | 3 | Chaves compostas: (id_municipio, ano) no PIB; (id_municipio, nome_rede) no IDEB; (4 colunas) na taxa_distorcao |

### Testes por modelo:

**Staging:**
| Modelo | not_null | unique | relationships | singular |
|--------|----------|--------|---------------|----------|
| stg_dtb | id_municipio | id_municipio | — | — |
| stg_pib_municipios | id_municipio, ano_competencia | — | → stg_dtb | unique_combination |
| stg_projetos_ia | ano_competencia | — | — | — |
| stg_ideb | id_municipio | — | → stg_dtb | unique_combination |
| stg_taxa_distorcao | id_municipio, ano_competencia, categoria_localidade, dependencia_administrativa | — | → stg_dtb | unique_combination |

**Core:**
| Modelo | not_null | unique | relationships |
|--------|----------|--------|---------------|
| dim_localidade | sk_localidade, id_municipio, id_uf | sk_localidade, id_municipio | — |
| dim_rede | sk_rede | sk_rede, id_rede | — |
| fato_ideb | sk_localidade, sk_rede, ano | — | → dim_localidade, dim_rede |
| fato_projetos_ia | sk_localidade, ano, quantidade_projetos, quantidade_beneficiados | — | → dim_localidade |
| fato_socioeconomica | sk_localidade, ano | — | → dim_localidade |
| fato_taxa_distorcao_municipio | sk_localidade, ano | — | → dim_localidade |
| fato_taxa_distorcao_rede_categoria | sk_localidade, sk_rede, ano | — | → dim_localidade, dim_rede |

### Diagnóstico de falhas

**`not_null_stg_projetos_ia_nome_municipio` FAIL:**
- Causa: raw.projetos_ia tem NULLs legítimos em nome_municipio
- Ação: Remover `not_null` do schema.yml (staging é 1:1)

**`relationships_fato_projetos_ia_sk_localidade` FAIL:**
- Causa: SK no fato não encontrada na dimensão (nome_municipio + nome_uf sem match)
- Ação: Verificar CASE WHEN de limpeza ou uf_mapping

**`unique_dim_localidade_sk_localidade` FAIL:**
- Causa: MD5 collision ou DISTINCT mal aplicado
- Ação: Verificar se há id_municipio duplicado em stg_dtb

---

## Troubleshooting

### `dbt debug` falha
```bash
cat ~/.dbt/profiles.yml
# Verificar host, user, password, sslmode: require
```

### `dbt run` falha em um modelo
```bash
dbt run --select stg_dtb -vv        # Verboso, mostra SQL compilado
# Verificar target/compiled/ para o SQL exato
```

### Teste de integridade referencial falha
```sql
-- Encontrar chaves órfãs
SELECT f.sk_localidade
FROM dev.fato_projetos_ia f
LEFT JOIN dev.dim_localidade d ON d.sk_localidade = f.sk_localidade
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
| `dev` | `dev` | Desenvolvimento, testes |
| `prod` | `public` | Produção, dashboards Metabase |

```bash
dbt run --target prod     # Cria em schema public
dbt test --target prod    # Testa produção
```

# 🔧 Guia Interno: Fluxo e Execução do Pipeline dbt

## 📋 Índice
1. [Visão Geral do Fluxo](#visão-geral-do-fluxo)
2. [Estrutura do Projeto dbt](#estrutura-do-projeto-dbt)
3. [Explicação Detalhada das Camadas](#explicação-detalhada-das-camadas)
4. [Pré-requisitos e Instalação](#pré-requisitos-e-instalação)
5. [Executando o Pipeline](#executando-o-pipeline)
6. [Documentação dos Modelos](#documentação-dos-modelos)
7. [Testes e Validação](#testes-e-validação)
8. [Troubleshooting](#troubleshooting)

---

## 🔄 Visão Geral do Fluxo

O pipeline segue o padrão **ELT (Extract, Load, Transform)** com duas camadas de transformação. Os arquivos Parquet são lidos diretamente pelo DuckDB via macro `{{ parquet() }}`:

```
                ┌─────────────────────────────────────────────────────────────┐
                │          DADOS PROCESSADOS EM PARQUET (data/processed/)     │
                │   dtb_municipios.parquet, pib_municipios.parquet, etc      │
                └──────────────────────────┬──────────────────────────────────┘
                                           │
                          {{ parquet('nome') }} → read_parquet()
                                           ↓
                ┌─────────────────────────────────────────────────────────────┐
                │        CAMADA STAGING (VIEW - stg_* models)                 │
                │    stg_dtb.sql, stg_pib_municipios.sql, etc                │
                │  • Leitura direta dos Parquets via DuckDB                   │
                │  • Limpeza, casting, validação                             │
                │  • Enriquecimento (lookups, concatenações)                 │
                └──────────────────────────┬──────────────────────────────────┘
                                           │
                                     dbt run --target dev
                                           ↓
                ┌─────────────────────────────────────────────────────────────┐
                │        CAMADA CORE (TABLE - modelo Kimball)                 │
                │  ┌────────────────────────────────────────────────────────┐ │
                │  │ DIMENSÕES: dim_localidade, dim_calendario, dim_rede   │ │
                │  └────────────────────────────────────────────────────────┘ │
                │  ┌────────────────────────────────────────────────────────┐ │
                │  │ FATOS: fato_projetos_ia, fato_pib_municipios,         │ │
                │  │   fato_ideb_municipios, fato_taxa_distorcao_municipio,│ │
                │  │   fato_taxa_distorcao_rede_categoria                  │ │
                │  └────────────────────────────────────────────────────────┘ │
                └──────────────────────────┬──────────────────────────────────┘
                                           │
                                     dbt test --target dev
                                           ↓
                ┌─────────────────────────────────────────────────────────────┐
                │          VALIDAÇÃO (53 testes automáticos)                  │
                │  • Unicidade, integridade referencial, not null            │
                └─────────────────────────────────────────────────────────────┘
```

---

## 📁 Estrutura do Projeto dbt

```
dbt_transformations/
├── dbt_project.yml                      # Configuração principal (profile, versão, etc)
├── README.md                            # Quick start (leia primeiro!)
├── GUIA_INTERNO.md                      # Este arquivo (documentação completa)
│
├── macros/                              # Funções reutilizáveis SQL
│   ├── parquet.sql                      # Macro de leitura de Parquet (read_parquet)
│   ├── safe_cast.sql                    # Casting seguro com tratamento de nulos
│   └── project_metric.sql               # Pivotamento de colunas de projetos
│
├── models/
│   ├── staging/                         # CAMADA 1: Views - leitura direta do Parquet
│   │   ├── stg_schema.yml               # Testes do staging (unique, not_null)
│   │   ├── stg_dtb.sql                  # Staging da DTB
│   │   ├── stg_pib_municipios.sql       # Staging do PIB (casting NUMERIC)
│   │   ├── stg_projetos_ia.sql          # Staging com lookup IBGE + data cleansing
│   │   └── stg_taxa_distorcao.sql       # Staging com safe_cast de taxas
│   │
│   └── core/                            # CAMADA 2: Tables - modelo dimensional Kimball
│       ├── schema.yml                   # Documentação + testes de integridade
│       ├── dim_localidade.sql           # DIMENSÃO: 1 linha por município
│       ├── dim_calendario.sql           # DIMENSÃO: 1 linha por ano (2000-2031)
│       ├── dim_rede.sql                 # DIMENSÃO: 1 linha por tipo de rede
│       ├── fato_projetos_ia.sql         # FATO: projetos IA (município + ano)
│       ├── fato_pib_municipios.sql      # FATO: PIB e VA (município + ano)
│       ├── fato_ideb_municipios.sql     # FATO: IDEB (município + rede + ano)
│       ├── fato_taxa_distorcao_municipio.sql      # FATO: distorção consolidado
│       └── fato_taxa_distorcao_rede_categoria.sql # FATO: distorção por rede/categoria
│
└── tests/                               # Testes customizados (vazio por enquanto)
    └── .gitkeep
```

**Ordem de execução:**
1. `python scripts/data_processing.py` → gera Parquets em `data/processed/`
2. `dbt run` → constrói staging (views) + core (tables)
3. `dbt test` → valida integridade


---

## 📚 Explicação Detalhada das Camadas

### 🟡 CAMADA STAGING (stg_*) — VIEW
**Objetivo**: Ler diretamente os Parquets via DuckDB, limpar, validar e enriquecer os dados

**Como funciona:**
- Cada modelo usa `{{ parquet('nome_arquivo') }}` que expande para `read_parquet('../data/processed/nome.parquet')`
- O DuckDB lê o arquivo Parquet direto do disco — sem carga prévia
- São views, não tabelas: nenhum dado é materializado no banco

#### **stg_dtb.sql** (Diretório Territorial)
- **Input**: `{{ parquet('dtb_municipios') }}` (5.571 municípios)
- **Transformações**:
  - Casting de IDs para INTEGER
  - UPPER e TRIM em nomes
  - Usa `sigla_uf` gerada no pré-processamento a partir do código numérico da UF
- **Output**: 5.571 linhas, colunas tipadas corretamente
- **Testes**: `unique` e `not_null` em `id_municipio`

#### **stg_pib_municipios.sql** (Produto Interno Bruto)
- **Input**: `{{ parquet('pib_municipios') }}` (66.825 linhas)
- **Transformações**:
  - Casting de ano e id_municipio para INTEGER
  - Casting de valores monetários para NUMERIC
  - Nomes descritivos para colunas (ex: `pib_agropecuaria`)
- **Output**: 66.825 linhas, 2010-2021, validadas

#### **stg_projetos_ia.sql** (Projetos Alpargatas)
- **Input**: `{{ parquet('projetos_ia') }}` (135 linhas cruas)
- **Transformações**:
  - **Data Cleansing**: Corrige nomes malformados
    - `'CAMPINA GRANDE- MIXING CENTER'` → `'CAMPINA GRANDE'`
    - `'QUEIMADAS *'` → `'QUEIMADAS'`
  - **Lookup com dicionário IBGE**: JOIN com `stg_dtb` para obter `id_municipio` oficial
  - **Pivotamento**: Soma colunas de projetos (5 variações)
  - **Agregação**: Total por município + ano
- **Output**: ~112 linhas (município + ano únicos)
- **Testes**: `not_null` em id_municipio, `relationships` com stg_dtb

#### **stg_taxa_distorcao.sql** (Educação)
- **Input**: `{{ parquet('taxa_distorcao') }}` (~327.944 linhas)
- **Transformações**:
  - Casting de ano e id_municipio para INTEGER
  - Safe casting de taxas (trata '--' como NULL)
  - Uppercase em categorizações
- **Output**: ~327.934 linhas (removidas as com CO_MUNICIPIO nulo)
- **Nota**: Mantém granularidade (categoria + dependência por município)

---

### 🟢 CAMADA CORE (modelo Kimball) — TABLE
**Objetivo**: Criar estrutura dimensional para análise. Tabelas materializadas fisicamente no banco.

#### **dim_localidade** (DIMENSÃO)
- **Granularidade**: 1 linha por município
- **Colunas**:
  - `sk_localidade` (PK): Hash MD5 do `id_municipio` oficial do IBGE
  - `id_municipio` (NK): Business Key (código IBGE)
  - Atributos: nome, UF, região geográfica
- **Input**: `stg_dtb` (5.571 linhas)
- **Testes**: `unique` e `not_null` em sk_localidade e id_municipio

#### **dim_calendario** (DIMENSÃO)
- **Granularidade**: 1 linha por ano (2000-2031)
- **Colunas**:
  - `sk_calendario` (PK): Hash MD5 do ano
  - `ano_referencia`: Ano de referência
- **Input**: Gerador recursivo (CTE)
- **Testes**: `unique` e `not_null` em sk_calendario e ano_referencia

#### **dim_rede** (DIMENSÃO)
- **Granularidade**: 1 linha por tipo de rede
- **Colunas**:
  - `sk_rede` (PK): Hash MD5 do nome_rede
  - `nome_rede`: Nome padronizado (FEDERAL, ESTADUAL, MUNICIPAL, PRIVADA, PÚBLICA, DESCONHECIDO)
  - `id_rede`: Código numérico (0=Pública, 2=Estadual, 4=Municipal, 6=Federal, 8=Privada, -1=Desconhecido)
  - `id_nome_rede`: Descrição composta
- **Input**: `{{ parquet('ideb_municipios') }}` + `stg_taxa_distorcao`
- **Testes**: `unique` e `not_null` em sk_rede e nome_rede

#### **fato_projetos_ia** (FATO)
- **Granularidade**: 1 linha por (município + ano)
- **Colunas**:
  - `sk_localidade` (FK), `sk_calendario` (FK)
  - `ano`: Ano de execução
  - `quantidade_projetos`: Métrica agregada
  - `quantidade_beneficiados`: Métrica agregada
- **Input**: `stg_projetos_ia` → JOIN dim_localidade
- **Testes**: `not_null` em colunas, `relationships` para FK

#### **fato_pib_municipios** (FATO)
- **Granularidade**: 1 linha por (município + ano)
- **Colunas**:
  - `sk_localidade` (FK), `sk_calendario` (FK), `ano`
  - `pib_agropecuaria`, `pib_industria`, `pib_servicos`, `pib_administracao_publica`
  - `pib_vab_total`, `pib_impostos`, `pib_total`, `pib_per_capita`
- **Input**: `stg_pib_municipios` → JOIN dim_localidade + dim_calendario
- **Testes**: `not_null` em colunas críticas, `relationships` para FK

#### **fato_ideb_municipios** (FATO)
- **Granularidade**: 1 linha por (município + rede + ano)
- **Colunas**:
  - `sk_localidade` (FK), `sk_rede` (FK), `sk_calendario` (FK)
  - `ideb_observado`, `ideb_projecao`, `nota_media_saeb`, `nota_matematica_saeb`, `nota_portugues_saeb`
  - `taxa_aprovacao_series_iniciais`, `taxa_aprovacao_*_ano`, `indicador_rendimento`
- **Input**: `{{ parquet('ideb_municipios') }}` → UNPIVOT + JOIN dimensoes
- **Nota**: Colunas VARCHAR do Parquet são convertidas via `TRY_CAST` para NUMERIC

#### **fato_taxa_distorcao_municipio** (FATO)
- **Granularidade**: 1 linha por (município + ano) — consolidado (categoria=TOTAL, dependência=TOTAL)
- **Colunas**:
  - `sk_localidade` (FK), `sk_calendario` (FK)
  - `taxa_distorcao_ensino_fundamental`, `taxa_distorcao_ensino_medio`
- **Input**: `stg_taxa_distorcao` → JOIN dim_localidade + dim_calendario

#### **fato_taxa_distorcao_rede_categoria** (FATO)
- **Granularidade**: 1 linha por (município + rede + categoria + ano)
- **Colunas**:
  - `sk_localidade` (FK), `sk_rede` (FK), `sk_calendario` (FK)
  - `categoria_localidade`, `taxa_distorcao_ensino_fundamental`, `taxa_distorcao_ensino_medio`
- **Input**: `stg_taxa_distorcao` → JOIN dim_localidade + dim_calendario + dim_rede
- **Nota**: Exclui registros consolidados (TOTAL/TOTAL)

---

## 📦 Pré-requisitos e Instalação

### Ferramentas Necessárias
1. **DuckDB** — Banco de dados analítico local (lê Parquets nativamente)
2. **dbt** com adaptador dbt-duckdb — Ferramenta de transformação
3. **Python 3.10+** — Para dbt e scripts auxiliares

### Setup Inicial

**1. Instalar dbt e dependências:**
```bash
cd dbt_transformations
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém:
- `dbt-duckdb` — Adaptador dbt para DuckDB
- `duckdb` — Banco de dados analítico

**2. Configurar conexão com DuckDB:**

O perfil já está configurado em `profiles.yml` para usar DuckDB local:
```yaml
alpargatas-impacto-educacional:
  outputs:
    dev:
      type: duckdb
      path: data/banco_dev.duckdb
      attach:
        - path: data/banco_prod.duckdb
          alias: prod
      threads: 4
  target: dev
```

**3. Testar conexão:**
```bash
dbt debug
```

Esperado: `All checks passed!`


---

## ⚙️ Executando o Pipeline

### Comandos Principais de dbt

#### **dbt parse** (Validação sem execução)
Valida a sintaxe YAML e SQL sem executar nada no banco:
```bash
dbt parse --target dev
```
- **Uso**: Rodar antes de `dbt run` para detectar problemas
- **Tempo**: ~5 segundos

#### **dbt run** (Executa transformações)
Constrói todas as tabelas (staging → core):
```bash
dbt run --target dev              # Modo padrão
dbt run --target prod             # Produção
dbt run --select dim_localidade   # Apenas um modelo
```
- Staging models → criados como **views**
- Core models → criados como **tables**
- Executa em paralelo (4 threads)
- Respeita dependências entre modelos
- **Tempo**: ~5 segundos (completo)

#### **dbt test** (Valida integridade)
Executa 53 testes automáticos:
```bash
dbt test --target dev
dbt test --select fato_projetos_ia  # Testes de um modelo
```
- Tests: unique, not_null, relationships
- **Tempo**: ~2 segundos

---

### ✅ Execução Completa (Recomendado)

**Ordem correta de execução:**

#### **Passo 1: Gerar Parquets processados**
```bash
cd dbt_transformations
python scripts/data_processing.py
```
- Lê os Excel brutos em `data/raw/` e grava Parquets em `data/processed/`

#### **Passo 2: Executar pipeline dbt**
```bash
dbt run --target dev
```
- Executa modelos em ordem de dependência
- Staging (views) → Core (tables)

- **Tempo esperado**: ~5 segundos
- **Output**: 12 modelos criados
  ```
  ✓ 4 staging views
  ✓ 8 core tables (3 dimensões + 5 fatos)
  ```

#### **Passo 3: Validar integridade**
```bash
dbt test --target dev
```

- Executa 53 testes automáticos
- **Tempo esperado**: ~2 segundos
- **Sucesso esperado**: `PASS=53 FAIL=0 ERROR=0`

#### **Passo 4 (Opcional): Gerar documentação interativa**
```bash
dbt docs generate --target dev
dbt docs serve
```

- Abre em `http://localhost:8000`
- Mostra lineage (DAG) de todos os modelos
- Exibe documentação de cada tabela/coluna
- Lista dependências

---

### 🔄 Execuções Subsequentes

**Se apenas o código SQL foi alterado:**
```bash
dbt parse --target dev      # Validar antes
dbt run --target dev        # Executar
dbt test --target dev       # Testar
```

**Se apenas os dados Parquet foram atualizados:**
```bash
dbt run --target dev        # Releitura automática das views
dbt test --target dev       # Validar
```
> Nota: Como staging são views, basta rodar `dbt run` — o DuckDB relê os Parquets automaticamente.

**Se quer recriar uma tabela específica:**
```bash
dbt run --select fato_projetos_ia --target dev
dbt test --select fato_projetos_ia --target dev
```

**Se quer executar um modelo e suas dependências:**
```bash
dbt run --select +dim_localidade --target dev   # Reconstrói dim + tudo que depende
```

---

## 📖 Documentação dos Modelos

### Consultar informações de um modelo

```bash
# Mostrar schema de uma tabela
dbt show --select dim_localidade

# Mostrar dependências
dbt run --select dim_localidade --graph

# Mostrar quem depende deste modelo
dbt run --select +dim_localidade
```

### Acessar documentação no código

Cada coluna tem descrição em `schema.yml`:
- Significado
- Tipo de teste
- Granularidade

---

## ✅ Testes e Validação

### Tipos de Testes Implementados

| Tipo | Quantidade | Descrição |
|------|-----------|-----------|
| `not_null` | 31 | Garante que colunas críticas não são nulas |
| `unique` | 10 | Chaves primárias e chaves naturais únicas (sk_localidade, id_municipio, sk_calendario, sk_rede, id_rede, etc) |
| `relationships` | 12 | FKs apontam para PKs existentes |
| **Total** | **53** | - |

### Executar testes específicos

```bash
# Testar apenas dim_localidade
dbt test --select dim_localidade

# Testar apenas integridade referencial
dbt test --select tag:relationships

# Testar com verbosidade (mostra SQL)
dbt test --select dim_localidade -vv
```

### Interpretando falhas

**Erro: `relationships_fato_projetos_ia_sk_localidade...FAIL`**
- Significa: Existem SKs na fato que não existem na dimensão
- **Solução**: Verificar JOINs em `fato_projetos_ia.sql`

**Erro: `unique_dim_localidade_sk_localidade...FAIL`**
- Significa: Há SKs duplicadas na dimensão
- **Solução**: Verificar lógica de deduplicação em `dim_localidade.sql`

---

## 🐛 Troubleshooting

### Problema: `dbt debug` falha

**Solução 1**: Verificar se o DuckDB está instalado
```bash
pip install duckdb dbt-duckdb
```

**Solução 2**: Verificar o caminho do banco
```bash
# O path está em profiles.yml ou dbt_project.yml
ls data/banco_dev.duckdb
```

---

### Problema: `dbt run` falha em uma tabela

**Passo 1**: Ver erro completo
```bash
dbt run -vv
```

**Passo 2**: Verificar se o arquivo Parquet existe
```bash
ls data/processed/*.parquet
```

**Passo 3**: Verificar dependências
```bash
dbt run --select stg_dtb --graph
```

---

### Problema: `dbt test` falha em integridade referencial

**Diagnóstico**:
```sql
-- Encontrar chaves órfãs (no DuckDB)
SELECT COUNT(*) FROM fato_projetos_ia f 
WHERE NOT EXISTS (SELECT 1 FROM dim_localidade d WHERE d.sk_localidade = f.sk_localidade);
```

**Se > 0**: Há dados inválidos. Verificar JOIN no modelo.

---

### Problema: DuckDB arquivo travado

**Causa**: Outro processo (ex: Metabase) está com o arquivo `banco_dev.duckdb` aberto.

**Solução**: Fechar o processo que está usando o banco, ou:
```bash
# Windows - encontrar e encerrar o processo
tasklist | findstr java
taskkill /PID <pid> /F
```

---

## 📞 Suporte

- **Dúvidas sobre dbt**: https://docs.getdbt.com/
- **Dúvidas sobre DuckDB**: https://duckdb.org/docs/
- **Logs**: Verificar `target/logs/dbt.log`

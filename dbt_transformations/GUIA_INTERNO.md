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

O pipeline segue o padrão **ELT (Extract, Load, Transform)** com três camadas bem definidas:

```
┌─────────────────────────────────────────────────────────────┐
│              DADOS BRUTOS EM PARQUET (data/raw/)            │
│   (dtb_municipios.parquet, pib_municipios.parquet, etc)    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                load_raw_to_postgres.py
                (usa DuckDB para ler parquets)
                           ↓
┌─────────────────────────────────────────────────────────────┐
│          CAMADA RAW (raw schema no Postgres)               │
│    raw_dtb.sql, raw_pib_municipios.sql, etc                │
│  • Cria tabelas: raw.dtb_municipios, raw.pib_municipios    │
│  • Replicação 1:1 (sem transformação)                      │
│  • ⚠️  load_raw_to_postgres.py cria APENAS schema raw      │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    dbt run --target dev
                           ↓
┌─────────────────────────────────────────────────────────────┐
│        CAMADA STAGING (stg_* models)                        │
│    stg_dtb.sql, stg_pib_municipios.sql, etc                │
│  • Limpeza, casting, validação                             │
│  • Enriquecimento (lookups, concatenações)                 │
│  • Sem agregações ainda                                    │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    dbt run --target dev
                           ↓
┌─────────────────────────────────────────────────────────────┐
│        CAMADA CORE (modelo Kimball)                        │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ DIMENSÕES: dim_localidade                             │ │
│  └────────────────────────────────────────────────────────┘ │
│  ┌────────────────────────────────────────────────────────┐ │
│  │ FATOS: fato_projetos_ia, fato_socioeconomica,         │ │
│  │        fato_taxa_distorcao                            │ │
│  └────────────────────────────────────────────────────────┘ │
└──────────────────────────┬──────────────────────────────────┘
                           │
                    dbt test --target dev
                           ↓
┌─────────────────────────────────────────────────────────────┐
│          VALIDAÇÃO (23 testes automáticos)                 │
│  • Unicidade, integridade referencial, not null           │
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
│   ├── safe_cast.sql                    # Casting seguro com tratamento de nulos
│   └── parquet.sql                      # Exportação em parquet (futuro)
│
├── models/
│   ├── raw/                             # CAMADA 1: Dados brutos (sem transformação)
│   │   ├── raw_dtb.sql                  # → raw.dtb_municipios
│   │   ├── raw_pib_municipios.sql       # → raw.pib_municipios
│   │   ├── raw_projetos_ia.sql          # → raw.projetos_ia
│   │   └── raw_taxa_distorcao.sql       # → raw.taxa_distorcao
│   │
│   ├── staging/                         # CAMADA 2: Limpeza e validação
│   │   ├── sources.yml                  # Definição das fontes raw
│   │   ├── stg_schema.yml               # Testes do staging (unique, not_null)
│   │   ├── stg_dtb.sql                  # Staging da DTB
│   │   ├── stg_pib_municipios.sql       # Staging do PIB (casting NUMERIC)
│   │   ├── stg_projetos_ia.sql          # Staging com lookup IBGE + data cleansing
│   │   └── stg_taxa_distorcao.sql       # Staging com safe_cast de taxas
│   │
│   └── core/                            # CAMADA 3: Modelo dimensional (Kimball)
│       ├── schema.yml                   # Documentação + testes de integridade
│       ├── dim_localidade.sql           # DIMENSÃO: 1 linha por município
│       ├── fato_projetos_ia.sql         # FATO: projetos IA (município + ano)
│       ├── fato_socioeconomica.sql      # FATO: PIB e VA (município + ano)
│       └── fato_taxa_distorcao.sql      # FATO: taxa distorção (município + ano + categoria + dependência)
│
├── scripts/
│   └── load_raw_to_postgres.py          # Script Python: carrega Parquets → raw schema
│                                         # Usa DuckDB para ler .parquet
│                                         # ⚠️  Cria APENAS schema raw (não é dbt run)
│
└── tests/                               # Testes customizados (vazio por enquanto)
    └── .gitkeep
```

**Ordem de execução:**
1. `load_raw_to_postgres.py` → cria schema `raw`
2. `dbt run` → constrói staging + core
3. `dbt test` → valida integridade


---

## 📚 Explicação Detalhada das Camadas

### 🔴 CAMADA RAW (raw_*)
**Objetivo**: Replicar os dados exatamente como vêm dos Parquets

**Como funciona:**
1. Script Python `load_raw_to_postgres.py` executa:
   - Lê cada `.parquet` em `data/raw/` usando **DuckDB**
   - Cria schema `raw` no Neon (se não existir)
   - Carrega dados em tabelas: `raw.dtb_municipios`, `raw.pib_municipios`, etc
   - **⚠️ Este script NÃO usa dbt, cria dados puros no Neon**

2. Modelos dbt `raw_*.sql` (4 modelos):
   - `raw_dtb.sql`: `SELECT * FROM raw.dtb_municipios` (sem transformação)
   - `raw_pib_municipios.sql`: Idem para PIB
   - `raw_projetos_ia.sql`: Idem para projetos
   - `raw_taxa_distorcao.sql`: Idem para taxa
   - **Objetivo**: Replicar 1:1 os dados raw no schema dbt

**Fluxo visual:**
```
data/raw/dtb_municipios.parquet
         ↓ (DuckDB lê)
load_raw_to_postgres.py
         ↓ (cria)
raw.dtb_municipios (tabela Postgres)
         ↓ (dbt replica)
raw_dtb.sql (modelo dbt)
```

**Quando executar:**
- Na primeira execução do projeto (1x)
- Quando os Parquets são atualizados
- Raramente - geralmente apenas initial setup

**Verificar se funcionou:**
```sql
-- No Postgres/Neon:
SELECT * FROM raw.dtb_municipios LIMIT 5;
SELECT COUNT(*) FROM raw.pib_municipios;
-- Se retorna dados, o script funcionou!
```

**Comando:**
```bash
# Na primeira vez
python scripts/load_raw_to_postgres.py --target dev --if-exists replace

# Sem recarregar dados
dbt run --select raw_dtb raw_pib_municipios raw_projetos_ia raw_taxa_distorcao
```

---

### 🟡 CAMADA STAGING (stg_*)
**Objetivo**: Limpar, validar e enriquecer os dados

**O que acontece em cada modelo:**

#### **stg_dtb.sql** (Diretório Territorial)
- **Input**: `raw.dtb_municipios` (5.571 municípios)
- **Transformações**:
  - Casting de IDs para INTEGER
  - UPPER e TRIM em nomes
- **Output**: 5.571 linhas, colunas tipadas corretamente
- **Testes**: `unique` e `not_null` em `id_municipio`

#### **stg_pib_municipios.sql** (Produto Interno Bruto)
- **Input**: `raw.pib_municipios` (66.825 linhas)
- **Transformações**:
  - Casting de ano e id_municipio para INTEGER
  - Casting de valores monetários para NUMERIC
  - Nomes descritivos para colunas (ex: `pib_agropecuaria`)
- **Output**: 66.825 linhas, 2010-2021, validadas
- **Testes**: `not_null` em ano e id_municipio

#### **stg_projetos_ia.sql** (Projetos Alpargatas)
- **Input**: `raw.projetos_ia` (135 linhas cruas)
- **Transformações**:
  - **Data Cleansing**: Corrige nomes malformados
    - `'CAMPINA GRANDE- MIXING CENTER'` → `'CAMPINA GRANDE'`
    - `'QUEIMADAS *'` → `'QUEIMADAS'`
  - **Lookup com dicionário IBGE**: JOIN com `stg_dtb` para obter `id_municipio` oficial
  - **Pivotamento**: Soma colunas de projetos (5 variações)
  - **Agregação**: Total por município + ano
- **Output**: 112 linhas (município + ano únicos)
- **Testes**: `not_null` em id_municipio (via relationship)

#### **stg_taxa_distorcao.sql** (Educação)
- **Input**: `raw.taxa_distorcao` (327.944 linhas)
- **Transformações**:
  - Casting de ano e id_municipio para INTEGER
  - Safe casting de taxas (trata '--' como NULL)
  - Uppercase em categorizações
- **Output**: 327.934 linhas (removidas as com CO_MUNICIPIO nulo)
- **Nota**: Mantém granularidade (categoria + dependência por município)

---

### 🟢 CAMADA CORE (modelo Kimball)
**Objetivo**: Criar estrutura dimensional para análise

#### **dim_localidade** (DIMENSÃO)
- **Granularidade**: 1 linha por município
- **Colunas**:
  - `sk_localidade` (PK): Numérica sequencial (row_number)
  - `id_municipio` (NK): Business Key
  - Atributos: nome, UF, região geográfica
- **Input**: `stg_dtb` (5.571 linhas)
- **Output**: `dim_localidade` (5.571 linhas)
- **Testes**: `unique` e `not_null` em sk_localidade

#### **fato_projetos_ia** (FATO)
- **Granularidade**: 1 linha por (município + ano)
- **Colunas**:
  - `sk_localidade` (FK): Referencia dim_localidade
  - `ano`: Ano de execução
  - `quantidade_projetos`: Métrica agregada
  - `quantidade_beneficiados`: Métrica agregada
- **Input**: `stg_projetos_ia`
- **Output**: 112 linhas
- **Lógica**: JOIN stg_projetos_ia → dim_localidade, depois agrega por município+ano
- **Testes**: `not_null` em colunas, `relationships` para FK

#### **fato_socioeconomica** (FATO)
- **Granularidade**: 1 linha por (município + ano)
- **Colunas**:
  - `sk_localidade` (FK): Referencia dim_localidade
  - `ano`: Ano de referência
  - `va_bruto_agropecuaria` até `va_bruto_total`: Valor adicionado por setor
  - `impostos_liquidos`: Diferença PIB - VAB
  - `pib_total`: Métrica final
- **Input**: `stg_pib_municipios`
- **Output**: 66.825 linhas (todos os municípios × anos)
- **Nota**: PIB per capita removido (sem dados populacionais)
- **Testes**: `not_null` em colunas críticas, `relationships` para FK

#### **fato_taxa_distorcao** (FATO)
- **Granularidade**: 1 linha por (município + ano + categoria_localidade + dependencia_administrativa)
- **Colunas**:
  - `sk_localidade` (FK): Referencia dim_localidade
  - `ano`: Ano do censo
  - `categoria_localidade`: Urbana/Rural
  - `dependencia_administrativa`: Federal/Estadual/Municipal/Privada
  - `taxa_distorcao_ensino_fundamental`: Métrica (0-100%)
  - `taxa_distorcao_ensino_medio`: Métrica (0-100%)
- **Input**: `stg_taxa_distorcao`
- **Output**: 327.934 linhas
- **Nota**: Mantém granularidade máxima (não agrega)
- **Testes**: `not_null` em colunas críticas, `relationships` para FK

---

## 📦 Pré-requisitos e Instalação

### Ferramentas Necessárias
1. **Neon** (Postgres na nuvem) - Banco de dados
2. **dbt** - Ferramenta de transformação (v1.11+)
3. **Python 3.10+** - Para script de carregamento
4. **DuckDB** - Lê arquivos Parquet (usado em load_raw_to_postgres.py)

### Setup Inicial

**1. Instalar dbt e dependências:**
```bash
cd dbt_transformations
pip install -r requirements.txt
```

O arquivo `requirements.txt` contém:
- `dbt-postgres==1.10.1` - Adaptador dbt para Postgres
- `duckdb==1.5.4` - Leitura de arquivos .parquet

**2. Configurar conexão com Neon:**

Criar arquivo `~/.dbt/profiles.yml`:
```yaml
alpargatas-impacto-educacional:
  outputs:
    dev:
      type: postgres
      host: [seu-host-neon]
      user: [seu-usuario]
      password: [sua-senha]
      port: 5432
      dbname: neondb              # Nome do banco (padrão Neon)
      schema: dev                 # Schema onde os modelos serão criados
      threads: 4                  # Paralelização
      keepalives_idle: 0          # Manter conexão ativa
      sslmode: require            # SSL obrigatório para Neon
  target: dev                     # Target padrão
```

### Targets: dev vs prod

O arquivo `profiles.yml` suporta múltiplos targets:

```yaml
alpargatas-impacto-educacional:
  outputs:
    dev:                          # Desenvolvimento (schema: dev)
      type: postgres
      ...
      schema: dev
    
    prod:                         # Produção (schema: public)
      type: postgres
      ...
      schema: public
  
  target: dev                     # Target padrão (desenvolvimento)
```

**Executar com targets diferentes:**
```bash
dbt run --target dev              # Executa em dev (padrão)
dbt run --target prod             # Executa em prod
dbt test --target dev             # Testa dev
dbt parse --target prod           # Parse apenas de prod
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
- Lê `dbt_project.yml`, `schema.yml`, todos os `.sql`
- Detecta erros de YAML, referências circulares, sintaxe
- **Uso**: Rodar antes de `dbt run` para detectar problemas
- **Tempo**: ~5 segundos

#### **dbt run** (Executa transformações)
Constrói todas as tabelas (raw → staging → core):
```bash
dbt run --target dev              # Modo padrão
dbt run --target prod             # Produção
dbt run --select dim_localidade   # Apenas um modelo
```
- Executa em paralelo (4 threads por padrão)
- Respeita dependências entre modelos
- **Tempo**: ~15 segundos (completo)

#### **dbt test** (Valida integridade)
Executa 23 testes automáticos:
```bash
dbt test --target dev
dbt test --select fato_projetos_ia  # Testes de um modelo
```
- Tests: unique, not_null, relationships
- **Tempo**: ~10 segundos

---

### ✅ Execução Completa (Recomendado)

**Ordem correta de execução:**

#### **Passo 1: Validar sintaxe (opcional mas recomendado)**
```bash
cd dbt_transformations
dbt parse --target dev
```
- **Output esperado**: `Parsing complete` sem erros
- **Tempo**: ~5 segundos

#### **Passo 2: Carregar dados brutos (1x apenas)**
```bash
python scripts/load_raw_to_postgres.py --target dev --if-exists replace
```

**O que esse script faz:**
- Lê cada `.parquet` em `data/raw/`
- Usa **DuckDB** para ler parquets
- Cria schema `raw` no Neon (se não existir)
- Carrega dados para tabelas raw:
  - `raw.dtb_municipios` (5.571 linhas)
  - `raw.pib_municipios` (66.825 linhas)
  - `raw.projetos_ia` (135 linhas)
  - `raw.taxa_distorcao` (327.944 linhas)

**⚠️ IMPORTANTE:** Este script **NÃO é um modelo dbt**. Ele cria apenas o schema raw. Os modelos `raw_*.sql` (modelos dbt) apenas replicam essas tabelas.

**Verificar se funcionou:**
```sql
SELECT * FROM raw.dtb_municipios LIMIT 5;    -- Deve retornar 5 linhas
SELECT COUNT(*) FROM raw.pib_municipios;     -- Deve retornar 66825
```

**Opções:**
```bash
# Se já existem dados e quer recarregar
python scripts/load_raw_to_postgres.py --target dev --if-exists replace

# Se quer apenas validar sem substituir
python scripts/load_raw_to_postgres.py --target dev --if-exists skip

# Falhar se a tabela já existe (padrão)
python scripts/load_raw_to_postgres.py --target dev --if-exists fail
```

#### **Passo 3: Executar pipeline dbt**
```bash
dbt run --target dev
```

- Executa modelos em ordem de dependência
- Raw models (simples replicação de raw schema)
- Staging models (limpeza, validação)
- Core models (dimensões, fatos)

- **Tempo esperado**: ~15 segundos
- **Output**: 12 tabelas criadas
  ```
  ✓ 4 raw tables
  ✓ 4 staging tables
  ✓ 4 core tables (1 dimensão + 3 fatos)
  ```

#### **Passo 4: Validar integridade**
```bash
dbt test --target dev
```

- Executa 23 testes automáticos
- **Tempo esperado**: ~10 segundos
- **Sucesso esperado**: `PASS=23 FAIL=0 ERROR=0`

#### **Passo 5 (Opcional): Gerar documentação interativa**
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

**Se apenas os dados foram atualizados (novos parquets):**
```bash
python scripts/load_raw_to_postgres.py --target dev --if-exists replace
dbt run --target dev
dbt test --target dev
```

**Se apenas o código SQL foi alterado:**
```bash
dbt parse --target dev      # Validar antes
dbt run --target dev        # Executar
dbt test --target dev       # Testar
```

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

Cada modelo tem comentário no topo:
```sql
{{ config(materialized='table') }}
-- Exemplo de dim_localidade
```

Cada coluna tem descrição em `schema.yml`:
- Significado
- Tipo de teste
- Granularidade

---

## ✅ Testes e Validação

### Tipos de Testes Implementados

| Tipo | Quantidade | Descrição |
|------|-----------|-----------|
| `not_null` | 12 | Garante que colunas críticas não são nulas |
| `unique` | 3 | Chaves primárias (sk_localidade, id_municipio) |
| `relationships` | 3 | FKs apontam para PKs existentes |
| **Total** | **23** | - |

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
- **Solução**: Verificar row_number() em `dim_localidade.sql`

---

## 🐛 Troubleshooting

### Problema: `dbt debug` falha

**Solução 1**: Verificar `profiles.yml`
```bash
cat ~/.dbt/profiles.yml | grep alpargatas
```

**Solução 2**: Testar conexão direta com Postgres
```bash
psql -h [host] -U [user] -d alpargatas
```

---

### Problema: `dbt run` falha em uma tabela

**Passo 1**: Ver erro completo
```bash
dbt run -vv
```

**Passo 2**: Testar SQL manualmente
```sql
-- No Postgres
SELECT * FROM dev.stg_dtb LIMIT 5;
```

**Passo 3**: Verificar dependências
```bash
dbt run --select stg_dtb --graph
```

---

### Problema: `dbt test` falha em integridade referencial

**Diagnóstico**:
```sql
-- Encontrar chaves órfãs
SELECT COUNT(*) FROM dev.fato_projetos_ia f 
WHERE NOT EXISTS (SELECT 1 FROM dev.dim_localidade d WHERE d.sk_localidade = f.sk_localidade);
```

**Se > 0**: Há dados inválidos. Verificar JOIN no modelo.

---

## 📊 Próximos Passos

1. **Visualização**: Conectar Metabase/Tableau às tabelas `core`
2. **Incremental**: Adicionar models incrementais para dados que crecem diariamente
3. **Testes customizados**: Adicionar testes de qualidade de dados (ex: anomalias)
4. **Orquestração**: Usar Airflow/dbt Cloud para scheduler automático
5. **CI/CD**: Configurar testes automáticos em PRs via GitHub Actions

---

## 📞 Suporte

- **Dúvidas sobre dbt**: https://docs.getdbt.com/
- **Problemas com Postgres**: Verificar logs em `target/logs/dbt.log`
- **Problemas com Python**: Garantir virtualenv ativado (`source .venv/bin/activate`)

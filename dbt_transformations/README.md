# 🔄 dbt Transformations

Transformação de dados educacionais e socioeconômicos usando **dbt** com modelo dimensional de Kimball.

---

## 🚀 Quick Start

### 1. Instale as dependências
```bash
pip install -r requirements.txt
```

### 2. Configure a conexão
Crie `~/.dbt/profiles.yml`:
```yaml
alpargatas-impacto-educacional:
  outputs:
    dev:
      type: postgres
      host: seu-host
      user: seu-usuario
      password: sua-senha
      port: 5432
      dbname: alpargatas
      schema: dev
      threads: 4
  target: dev
```

### 3. Carregue os dados brutos
```bash
python scripts/load_raw_to_postgres.py --target dev --if-exists replace
```

### 4. Execute o pipeline
```bash
dbt run      # Constrói todos os modelos
dbt test     # Executa validações
```

---

## 📖 Documentação Completa

Para instruções detalhadas sobre a arquitetura, modelos, testes e troubleshooting, consulte o **[GUIA_INTERNO.md](./GUIA_INTERNO.md)**.

---

## 📊 Arquitetura

3 camadas de transformação:

```
raw (replicação)
    ↓
staging (limpeza + validação)
    ↓
core (modelo dimensional Kimball)
```

**Modelos**:
- **1 Dimensão**: `dim_localidade` (municípios)
- **3 Fatos**: `fato_projetos_ia`, `fato_socioeconomica`, `fato_taxa_distorcao`

**Validação**: 23 testes automáticos (uniqueness, referential integrity, not null)

---

## 🔍 Comandos Úteis

```bash
dbt run --select dim_localidade           # Executar um modelo específico
dbt test --select fato_projetos_ia        # Testar um modelo específico
dbt docs generate && dbt docs serve       # Gerar documentação interativa
dbt debug                                 # Verificar conexão
```

---

## 📋 Estrutura

```
├── models/
│   ├── raw/           # Replicação de dados brutos (4 modelos)
│   ├── staging/       # Limpeza e validação (4 modelos)
│   └── core/          # Modelo dimensional (1 dimensão + 3 fatos)
├── macros/            # Funções reutilizáveis
├── scripts/           # Load de dados (Python)
└── GUIA_INTERNO.md    # Documentação detalhada
```

---

## ⚠️ Pré-requisitos

- Postgres ou Neon com SSL habilitado
- Python 3.10+
- dbt 1.11+

**Para Neon**, adicione ao profile:
```yaml
sslmode: require
```

---

## 📚 Referência Rápida

| Comando | Descrição |
|---------|-----------|
| `dbt run` | Executa pipeline (raw → staging → core) |
| `dbt test` | Valida integridade de dados |
| `dbt docs serve` | Abre documentação interativa |
| `dbt debug` | Verifica conexão |

---

Para mais detalhes, veja **[GUIA_INTERNO.md](./GUIA_INTERNO.md)**.

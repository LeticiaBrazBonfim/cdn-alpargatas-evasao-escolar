# 🔄 dbt Transformations

Transformação de dados educacionais e socioeconômicos usando **dbt** com modelo dimensional de Kimball.

**⚠️ Apenas para desenvolvedores internos** - Requer acesso aos dados brutos e credenciais de banco.

---

## 📖 Documentação Completa

Para instruções detalhadas sobre a arquitetura, modelos, testes e manutenção, consulte o **[GUIA_INTERNO.md](./GUIA_INTERNO.md)**.

---

## 🏗️ Arquitetura

3 camadas de transformação:

```
Parquets em data/raw/
    ↓
raw (replicação 1:1)
    ↓
staging (limpeza + validação)
    ↓
core (modelo dimensional Kimball)
```

**Resultado**: 
- **1 Dimensão**: `dim_localidade` (5.571 municípios)
- **3 Fatos**: `fato_projetos_ia`, `fato_socioeconomica`, `fato_taxa_distorcao`
- **22 testes automáticos**: integridade, unicidade, referências

---

## 📚 Seções do GUIA_INTERNO.md

1. **Visão Geral**: Fluxo ELT completo
2. **Estrutura**: Organização de arquivos
3. **Camadas**: Explicação detalhada de cada modelo
4. **Pré-requisitos**: Ferramentas, setup, targets dev/prod
5. **Execução**: Comandos (parse, run, test, docs)
6. **Testes**: 23 validações automáticas
7. **Troubleshooting**: Diagnóstico e soluções

---

## 🔍 Comandos Principais

```bash
# Validar sintaxe (sem executar)
dbt parse --target dev

# Executar transformações
dbt run --target dev              # Desenvolvimento
dbt run --target prod             # Produção
dbt run --select fato_projetos_ia # Um modelo específico

# Validar integridade
dbt test --target dev

# Gerar documentação interativa
dbt docs generate --target dev
dbt docs serve
```

---

## 📋 Estrutura

```
├── models/
│   ├── raw/           # Replicação (4 modelos)
│   ├── staging/       # Limpeza (4 modelos)
│   └── core/          # Dimensional (4 modelos)
├── macros/            # Funções reutilizáveis
├── scripts/           # Python (carregamento)
└── GUIA_INTERNO.md    # Documentação completa
```

---

## ⚙️ Fluxo de Execução

1. **load_raw_to_postgres.py** - Carrega parquets → schema raw
2. **dbt run** - Constrói staging + core
3. **dbt test** - Valida 23 testes
4. **Metabase** - Consome tabelas finais

---

## 🔐 Configuração (Primeira Vez)

1. Instale dependências: `pip install -r requirements.txt`
2. Configure `~/.dbt/profiles.yml` com credenciais Neon
3. Execute: `python scripts/load_raw_to_postgres.py`
4. Execute: `dbt run && dbt test`

---

**👉 Veja [GUIA_INTERNO.md](./GUIA_INTERNO.md) para instruções completas.**

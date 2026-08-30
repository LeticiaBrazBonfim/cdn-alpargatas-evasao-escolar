# 📊 Dashboard Estratégico para o Instituto Alpargatas

[Metabase Dashboard](http://seu-metabase-url:3000) | [Documentação Técnica](dbt_transformations/GUIA_INTERNO.md) | [v1.0.0 Release](https://github.com/LeticiaBrazBonfim/cdn-alpargatas-evasao-escolar/releases/tag/v1.0.0)

Análise de dados educacionais e socioeconômicos para otimizar o impacto social e combater a evasão escolar nos municípios de atuação do Instituto Alpargatas.

---

## 📚 Contexto

Este projeto foi originalmente entregue como trabalho acadêmico na disciplina **Análise de Dados** (2025.1, UFPB). 

A partir da release [v1.0.0](https://github.com/LeticiaBrazBonfim/cdn-alpargatas-evasao-escolar/releases/tag/v1.0.0), o projeto evolui continuamente como um **laboratório pessoal** para aplicar e aprofundar conhecimentos em engenharia de dados, modelo dimensional e business intelligence.

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como uma solução de análise de dados para o **Instituto Alpargatas**, com o objetivo de aprimorar a eficácia de suas ações nos municípios atendidos.

A ferramenta integra dados públicos (IBGE, INEP) com dados privados do Instituto, oferecendo insights baseados em evidências através de um **dashboard no Metabase**. A análise permite:

- ✅ **Decisões Estratégicas**: Orientar o planejamento com dados consolidados e validados
- 🎯 **Ações Direcionadas**: Otimizar a alocação de recursos para regiões e públicos prioritários
- 🚀 **Maximização de Impacto Social**: Aumentar o alcance e eficiência das iniciativas educacionais

---

## 📊 Acessando o Dashboard

O dashboard em **Metabase** já está atualizado com os dados mais recentes. Você pode:

1. **Acessar**: [Metabase Dashboard](http://seu-metabase-url:3000)
2. **Visualizar**: Dashboards prontos com análises de impacto
3. **Explorar**: Dados por município, região, período
4. **Exportar**: Relatórios em PDF/Excel

**Não é necessário instalar nada** - o dashboard já consome os dados de produção.

---

## 📚 Fontes de Dados

O projeto integra múltiplas fontes de dados públicos e privados:

### Dados Públicos

- **INEP (Instituto Nacional de Estudos e Pesquisas Educacionais)**
  - Taxa de Distorção Idade-Série (2019-2023)
  - Índice de Desenvolvimento da Educação Básica (IDEB)

- **IBGE (Instituto Brasileiro de Geografia e Estatística)**
  - Produto Interno Bruto (PIB) Municipal (2010-2021)
  - Divisão Territorial Brasileira (municípios, UF, regiões)

### Dados Privados

- **Instituto Alpargatas**
  - Projetos de Inteligência Artificial Educacional
  - Dados de beneficiários e instituições atendidas (2020-2025)

---

## 💻 Arquitetura Técnica

O projeto utiliza o **modelo dimensional de Kimball** implementado em **dbt (data build tool)** para garantir qualidade, rastreabilidade e manutenibilidade dos dados:

```
data/processed/*.parquet (fonte de verdade)
    ↓
Camada STAGING (view - leitura direta via read_parquet)
    ↓
Camada CORE (table - modelo dimensional)
    ↓
Metabase (BI + Dashboards)
```

> **Decisão Arquitetural (2026-08-27):** A camada `raw` foi removida do pipeline dbt. Os arquivos `.parquet` em `data/processed/` são lidos diretamente pela camada staging através do macro `{{ parquet() }}`, que expande para `read_parquet()` do DuckDB. Isso elimina a materialização desnecessária de tabelas intermediárias no banco de dados e reduz a poluição visual no catálogo do BI. Para reverter esta decisão (ex: migração para Postgres/Neon), recrie a pasta `models/raw/`, o arquivo `models/staging/sources.yml` e substitua `{{ parquet() }}` por `{{ ref('raw_...') }}` nos modelos staging.

**53 testes automáticos** validam integridade, unicidade e consistência dos dados.

---

## 🔧 Documentação Técnica

Para desenvolvedores/analistas que precisam manter ou evoluir o projeto:

- **[Guia Interno Detalhado](dbt_transformations/GUIA_INTERNO.md)**: Fluxo completo do pipeline, modelos dbt, testes
- **[Schema de Dados](dbt_transformations/models/core/schema.yml)**: Documentação de cada tabela e coluna
- **[README dbt](dbt_transformations/README.md)**: Referência rápida de comandos

---

## 📋 Modelos de Dados

### Dimensões
- **dim_localidade**: Municípios, UF, Regiões Geográficas (5.571 linhas)
- **dim_calendario**: Dimensão temporal para séries históricas
- **dim_rede**: Tipologia de rede de ensino (Federal, Estadual, Municipal, Privada, Pública)

### Fatos (Métricas)

| Fato | Granularidade | Métricas |
|------|---|---|
| **fato_projetos_ia** | Município + Ano | Quantidade de projetos, Alunos beneficiados |
| **fato_pib_municipios** | Município + Ano | PIB, Valor Adicionado Bruto por setor |
| **fato_ideb_municipios** | Município + Rede + Ano | IDEB observado/projetado, Notas SAEB, Taxas de aprovação |
| **fato_taxa_distorcao_municipio** | Município + Ano | Taxa idade-série (Fundamental + Médio) |
| **fato_taxa_distorcao_rede_categoria** | Município + Rede + Categoria + Ano | Taxa idade-série por dependência administrativa |

---

## 📞 Suporte e Contribuição

Para dúvidas sobre o dashboard ou dados:
- **BI/Metabase**: Entre em contato com o time de BI
- **Dados/Modelos**: Veja a documentação técnica

Para melhorias no pipeline, abra uma [Issue](https://github.com/LeticiaBraz/cdn-alpargatas-evasao-escolar/issues) no repositório.

---

## 👨‍💻 Desenvolvimento

**Leticia Braz Bonfim** - [GitHub](https://github.com/LeticiaBraz)

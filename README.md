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
Dados Brutos (Parquets)
    ↓
Camada RAW (replicação 1:1)
    ↓
Camada STAGING (limpeza + validação)
    ↓
Camada CORE (modelo dimensional)
    ↓
Metabase (BI + Dashboards)
```

**23 testes automáticos** validam integridade, unicidade e consistência dos dados.

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

### Fatos (Métricas)

| Fato | Granularidade | Linhas | Métricas |
|------|---|---|---|
| **fato_projetos_ia** | Município + Ano | 112 | Quantidade de projetos, Alunos beneficiados |
| **fato_socioeconomica** | Município + Ano | 66.825 | PIB, Valor Adicionado Bruto (VA) por setor |
| **fato_taxa_distorcao** | Município + Ano + Categoria + Dependência | 327.934 | Taxa idade-série (Fundamental + Médio) |

---

## 📞 Suporte e Contribuição

Para dúvidas sobre o dashboard ou dados:
- **BI/Metabase**: Entre em contato com o time de BI
- **Dados/Modelos**: Veja a documentação técnica

Para melhorias no pipeline, abra uma [Issue](https://github.com/LeticiaBraz/cdn-alpargatas-evasao-escolar/issues) no repositório.

---

## 👨‍💻 Desenvolvimento

**Leticia Braz Bonfim** - [GitHub](https://github.com/LeticiaBraz)

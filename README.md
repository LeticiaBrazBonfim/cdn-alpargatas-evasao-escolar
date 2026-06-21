# 📊 Dashboard Estratégico para o Instituto Alpargatas

[Streamlit App](https://cdn-alpargatas-evasao-escolar-dpzbhnwlezpeqy3vbyzbc3.streamlit.app/)

Análise de dados educacionais e socioeconômicos para otimizar o impacto social e combater a evasão escolar nos municípios de atuação do Instituto Alpargatas.

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como uma solução de análise de dados para o **Instituto Alpargatas**, com o objetivo de aprimorar a eficácia de suas ações nos municípios atendidos.

A ferramenta integra dados públicos (IBGE, INEP) com dados privados do Instituto, oferecendo insights baseados em evidências através de um dashboard interativo. A análise permite:

- ✅ **Decisões Estratégicas**: Orientar o planejamento com dados consolidados e validados
- 🎯 **Ações Direcionadas**: Otimizar a alocação de recursos para regiões e públicos prioritários
- 🚀 **Maximização de Impacto Social**: Aumentar o alcance e eficiência das iniciativas educacionais

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

> **Observação**: Os dados de PIB e contexto socioeconômico referem-se ao ano 2021 (último disponível). Para análises comparativas com anos subsequentes, o valor de 2021 foi replicado mantendo a consistência metodológica.

---

## 💻 Arquitetura Técnica

O projeto utiliza o **modelo dimensional de Kimball** implementado em **dbt (data build tool)** com três camadas de transformação:

```
Dados Brutos (Parquets)
         ↓
    Camada RAW
    (Replicação 1:1)
         ↓
   Camada STAGING
   (Limpeza + Validação)
         ↓
    Camada CORE
 (Modelo Dimensional)
         ↓
    Dashboard/BI
```

### Tecnologias Utilizadas

- **dbt**: Transformação de dados com testes automáticos
- **Postgres/Neon**: Banco de dados relacional
- **Python**: Scripts de carregamento de dados
- **Streamlit**: Dashboard interativo
- **Altair & Plotly**: Visualizações

---

## 🚀 Início Rápido

### Pré-requisitos
- [Python 3.10+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- Acesso ao banco de dados Postgres/Neon

### Instalação e Execução

**1. Clone o repositório**
```bash
git clone https://github.com/LeticiaBraz/cdn-alpargatas-evasao-escolar.git
cd cdn-alpargatas-evasao-escolar
```

**2. Crie e ative o ambiente virtual**
```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# ou macOS/Linux
source .venv/bin/activate
```

**3. Instale as dependências**
```bash
pip install -r requirements.txt
```

**4. Configure a conexão com o banco de dados**

Crie o arquivo `~/.dbt/profiles.yml`:
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
  target: dev
```

**5. Execute o pipeline de dados**
```bash
cd dbt_transformations
python scripts/load_raw_to_postgres.py
dbt run
dbt test
```

**6. Inicie o dashboard**
```bash
streamlit run app_streamlit.py
```

O dashboard estará disponível em `http://localhost:8501`

---

## 📖 Documentação Adicional

- **[Guia Interno Detalhado](dbt_transformations/GUIA_INTERNO.md)**: Instruções completas sobre o pipeline, modelos e testes
- **[Schema de Dados](dbt_transformations/models/core/schema.yml)**: Documentação de cada tabela e coluna
- **Documentação dbt**: Execute `dbt docs serve` na pasta dbt_transformations para gerar documentação interativa

---

## 📁 Estrutura do Projeto

```
.
├── data/
│   └── raw/                      # Dados brutos em Parquet
├── dbt_transformations/
│   ├── models/
│   │   ├── raw/                  # Replicação de dados brutos
│   │   ├── staging/              # Limpeza e validação
│   │   └── core/                 # Modelo dimensional
│   ├── scripts/
│   │   └── load_raw_to_postgres.py
│   ├── GUIA_INTERNO.md          # Instruções detalhadas
│   └── dbt_project.yml
├── app_streamlit/               # Dashboard interativo
├── requirements.txt
└── README.md
```

---

## ✅ Pipeline de Dados

O pipeline executa automaticamente:

1. **Carregamento (Raw)**: Dados brutos são replicados no banco
2. **Limpeza (Staging)**: Tipagem, validação e enriquecimento
3. **Transformação (Core)**: Modelo dimensional com dimensões e fatos
4. **Testes**: 23 testes automáticos de integridade e qualidade
5. **Visualização**: Dashboard consome as tabelas finais

Todas as transformações são **rastreáveis, versionadas e testadas**.

---

## 📊 Principais Dimensões e Métricas

### Dimensões
- **Localidade**: Municípios, UF, Regiões Geográficas
- **Tempo**: Anos de execução

### Fatos (Métricas)

| Fato | Granularidade | Métricas Principais |
|------|---|---|
| **Projetos IA** | Município + Ano | Quantidade de projetos, Alunos beneficiados |
| **Socioeconômica** | Município + Ano | PIB, Valor Adicionado Bruto (VAB) por setor |
| **Taxa Distorção** | Município + Ano + Categoria | Taxa idade-série (Fundamental + Médio) |

---

## 🔄 Ciclo de Atualização

| Frequência | Dados | Responsável |
|---|---|---|
| **Trimestral** | PIB Municipal | IBGE |
| **Anual** | Taxa Distorção, IDEB | INEP |
| **Ad-hoc** | Projetos IA | Instituto Alpargatas |

Após cada atualização de dados brutos, execute:
```bash
cd dbt_transformations
python scripts/load_raw_to_postgres.py
dbt run && dbt test
```

---

## 🤝 Equipe de Desenvolvimento

- **Leticia Braz Bonfim** - [GitHub](https://github.com/LeticiaBraz)
- **Bianca Lavine da Silva Beserra** - [GitHub](https://github.com/lavine0524)
- **Kaio Vitor Martins** - [GitHub](https://github.com/kaiov63)

---

## 📞 Suporte e Contribuição

Para dúvidas, sugestões ou reportar problemas, abra uma [Issue](https://github.com/LeticiaBraz/cdn-alpargatas-evasao-escolar/issues) no repositório.

---

## 📜 Licença

Este projeto é desenvolvido para o Instituto Alpargatas. Consulte o arquivo `LICENSE` para mais informações.

# 📊 Dashboard Estratégico para o Instituto Alpargatas

[Streamlit App](https://cdn-alpargatas-evasao-escolar-dpzbhnwlezpeqy3vbyzbc3.streamlit.app/)


Análise de dados educacionais e socioeconômicos para otimizar o impacto social e combater a evasão escolar nos municípios de atuação do Instituto Alpargatas.

---

## 📝 Sumário

- [📊 Dashboard Estratégico para o Instituto Alpargatas](#-dashboard-estratégico-para-o-instituto-alpargatas)
  - [📝 Sumário](#-sumário)
  - [🎯 Sobre o Projeto](#-sobre-o-projeto)
  - [📚 Fontes de Dados](#-fontes-de-dados)
    - [💻 Tecnologias Utilizadas](#-tecnologias-utilizadas)
    - [🗂️ Estrutura do Projeto](#️-estrutura-do-projeto)
    - [🚀 Instalação e Execução](#-instalação-e-execução)
    - [🧑‍💻 Equipe de Desenvolvimento](#-equipe-de-desenvolvimento)

---

## 🎯 Sobre o Projeto

Este projeto foi desenvolvido como uma solução de análise de dados para o **Instituto Alpargatas**, com o objetivo de aprimorar a eficácia de suas ações nos municípios atendidos.

A ferramenta é um dashboard interativo que cruza dados públicos (IBGE, INEP) com dados privados do Instituto. A partir da análise de correlações, tendências históricas e comparações geográficas, a solução permite:

-   ✅ **Decisões Estratégicas**: Fornecer insights baseados em evidências para guiar o planejamento.
-   🎯 **Ações Direcionadas**: Otimizar a alocação de recursos, focando em alunos e regiões de maior vulnerabilidade.
-   🚀 **Maximização de Impacto Social**: Aumentar o alcance e a eficiência das iniciativas do Instituto.

---

## 📚 Fontes de Dados

O dashboard integra diversas fontes de dados para criar uma visão completa do cenário educacional e socioeconômico dos municípios:

-   **INEP (Instituto Nacional de Estudos e Pesquisas Educacionais):**
    -   Índice de Desenvolvimento da Educação Básica (IDEB) - Anos Iniciais (2005-2023).
    -   Taxa de Distorção Idade-Série (TDI) - Ensino Fundamental (2019-2023).
-   **IBGE (Instituto Brasileiro de Geografia e Estatística):**
    -   Produto Interno Bruto (PIB) Municipal (2010-2021).
    -   Divisão Territorial Brasileira (DTB) com a malha municipal.
-   **Instituto Alpargatas:**
    -   Dados internos sobre número de projetos, instituições atendidas e alunos beneficiados (2020-2025).

> **Observação Metodológica:** Como os dados públicos de PIB e População do IBGE possuem uma defasagem, os valores do último ano disponível (2021) foram replicados para os anos subsequentes (2022-2025) no dataset final. Esta abordagem garante a possibilidade de análises comparativas com os dados mais recentes do Instituto, mantendo um cenário socioeconômico consistente.

---

### 💻 Tecnologias Utilizadas

As seguintes tecnologias foram essenciais para a construção do projeto:

-   **Python**: Linguagem principal para toda a análise e desenvolvimento.
-   **Pandas**: Manipulação, limpeza e estruturação dos dados.
-   **Streamlit**: Criação do dashboard interativo e data app.
-   **Altair** & **Plotly**: Visualização de dados e geração de gráficos interativos (barras, linhas, dispersão e mapas).
-   **Streamlit Option Menu**: Componente para a barra de navegação do dashboard.
-   **Openpyxl**: Leitura de arquivos no formato `.xlsx`.
-   **PyArrow**: Leitura e escrita de arquivos de alta performance no formato `.parquet`.

---

### 🗂️ Estrutura do Projeto

O projeto segue uma estrutura organizada para garantir a reprodutibilidade e a manutenibilidade do código:

```

.
├── data/   
│   ├── raw/                # Contém os dados brutos (.xlsx, .csv, etc.).
│   └── processed/          # Onde os dados limpos e consolidados são salvos (.parquet).
├── nbs/                    # Notebooks de exploração e prototipagem.
├── src/                    # Código-fonte da aplicação.
│  ├── main.py
│  └── data_ingestion.py
│  └── data_processing.py
│  └── paths.py
│ 
├── app_streamlit           # Código-fonte do dashboard interativo.
├── .gitignore              # Arquivos a serem ignorados pelo Git.
├── requirements.txt        # Lista de dependências do projeto.
└── README.md

````

---

### 🚀 Instalação e Execução

Siga os passos abaixo para executar o projeto em sua máquina local.

**Pré-requisitos:** É necessário ter o [Python 3.10+](https://www.python.org/downloads/) e o [Git](https://git-scm.com/downloads) instalados.

**OBS:** O pipeline (main.py) funciona como o "construtor" do projeto. Ele lê os arquivos brutos, processa os dados e salva o arquivo final (data_final_consolidado.parquet) que será usado pelo dashboard. O pipeline só precisa ser executado uma vez ou quando os dados brutos/lógica do código forem alterados. O dashboard (dash_alpargatas.py) é o "visualizador", que apenas lê o arquivo já construído pelo pipeline para exibir as análises.

1.  **Clonando o Repositório**

    1.1. **Escolha o local:** No terminal, navegue até o local onde você quer salvar o projeto. Utilize `cd caminho/diretorio`.

    **Exemplo (Windows):**
    ```bash
    cd C:/Users/meu-nome/Desktop
    ```
    **Exemplo (macOS/Linux):**
    ```bash
    cd ~/Desktop
    ```

    1.2. **Clone o repositório:** Agora que você está na pasta correta, use o comando `git clone[link_do_repositorio]` para baixar o repositório do projeto. 
    
    ```bash
    git clone https://github.com/LeticiaBrazBonfim/cdn-alpargatas-evasao-escolar.git
    ```
    
    O comando acima criará uma nova pasta com o nome do repositório (`cdn-alpargatas-evasao-escolar`) no local escolhido.
    Utilize `cd` para entrar em (`cdn-alpargatas-evasao-escolar`)

2.  **Ambiente Virtual**
    
    Para garantir a correta execução do programa é necessário criar um ambiente virtual e ativá-lo.

    2.1. **Criando o ambiente**
    ```bash
    python -m venv .venv
    ```
    
    2.2. **Ativando o ambiente**

    **No Windows:**
    ```bash
    source .venv/Scripts/activate
    ```

   Por padrão, o Windows pode bloquear a execução do script de ativação. Se você receber um erro, abra o PowerShell como Administrador e execute o comando abaixo para permitir a execução de scripts locais:

    ```powershell
    Set-ExecutionPolicy RemoteSigned
    ```
   Após o comando, feche o terminal e abra o do git bash para executar o comando de ativação do ambiente virtual novamente.

    **No MacOS/Linux:**
    ```bash
    source .venv/bin/activate
    ```

3.  **Instalando as Dependências**
    
    ```bash
    pip install -r requirements.txt
    ```

4.  **Executando o Pipeline de Dados**
    
    ```bash
    python src/main.py  
    ```
    
5.  **Iniciando o Dashboard**
    ```bash
    streamlit run app_streamlit.py
    ```

---

### 🧑‍💻 Equipe de Desenvolvimento

* **Leticia Braz Bonfim** - [leticia.bonfim@academico.ufpb.br](mailto:leticia.bonfim@academico.ufpb.br) - [GitHub](https://github.com/Leticiabraz)
* **Bianca Lavine da Silva Beserra** - [bianca.lavine@academico.ufpb.br](mailto:bianca.lavine@academico.ufpb.br) - [GitHub](https://github.com/lavine0524)
* **Kaio Vitor Martins** - [kvms@academico.ufpb.br](mailto:kvms@academico.ufpb.br) - [GitHub](https://github.com/kaiov63)

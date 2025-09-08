# 📊 Dashboard de Análise de Dados: Instituto Alpargatas

O projeto foi desenvolvido como um projeto de extensão para a disciplina de Análise de Dados, ministrada pelo professor Dr. Aléssio Tony C. Almeida, no curso de Ciência de Dados para Negócios na UFPB e tem como objetivo aprimorar as ações do Instituto Alpargatas nos municípios em que ele atua.

A solução é uma ferramenta interativa que garante:

-   **Decisões Estratégicas**: Tomadas de decisão ágeis e totalmente baseadas em dados.
-   **Ações Direcionadas**: Otimiza o uso de recursos para focar em alunos e regiões de maior vulnerabilidade.
-   **Maximização de Impacto Social**: Aumenta o alcance da instituição com o uso inteligente dos recursos.

A ferramenta integra bases de dados públicas (IBGE e IDEB) e privadas (do Instituto Alpargatas) para identificar os fatores que contribuem para a evasão escolar. Com uma abordagem focada na análise de correlação, exploratória e cluster de dados, o projeto permite explorar o desempenho educacional e sua correlação com fatores socioeconômicos em nível municipal, apresentando os resultados por meio de gráficos e métricas visuais. 

---

## 📝 Sumário

- [Dashboard de Análise de Dados: Alpargatas](#dashboard-de-análise-de-dados-alpargatas)
- [Tecnologias](#tecnologias)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Executar](#como-executar)
- [Equipe de Desenvolvimento](#equipe-de-desenvolvimento)

---

### 💻 Tecnologias

As seguintes tecnologias foram utilizadas para o desenvolvimento deste projeto:

-   **Python**: A linguagem de programação principal.
-   **Streamlit**: Para a criação do dashboard interativo.
-   **Pandas**: Essencial para a manipulação e análise dos dados.
-   **Matplotlib** & **Seaborn**: Para a visualização dos dados e geração de gráficos.
-   **python-dotenv**: Para o gerenciamento de variáveis de ambiente.
-   **Altair**

---

### 🗂️ Estrutura do Projeto

A organização do projeto segue uma estrutura padrão para ciência de dados, garantindo reprodutibilidade e clareza:

```

.
├── data/                    \# Contém dados brutos e processados.
├── notebooks/               \# Notebooks de exploração e prototipagem.
├── src/                     \# Código-fonte da aplicação.
│   ├── dash_alpargatas.py
|   └── data_ingestion.py
│   └── data_processing.py
|   └── paths.py
├── .env                     \# Variáveis de ambiente (caminhos de arquivos).
├── .gitignore               \# Arquivos a serem ignorados pelo Git.
├── requirements.txt         \# Lista de dependências do projeto.
└── README.md

````

---

### 🚀 Como Executar

Siga os passos abaixo para rodar a aplicação em sua máquina local.

**OBS:** Certifique-se de ter Python 3.10+ e Git instalados em seu sistema.

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

2.  **Ambiente Virtual**
    
    Para garantir a correta execução do programa é necessário criar um ambiente virtual e ativá-lo.

    2.1. **Criando o ambiente**
    ```bash
    python -m venv .venv
    ```
    
    2.2. **Ativando o ambiente**
    * **No Windows:**
        ```bash
        .\.venv\Scripts\activate
        ```
    * **No macOS/Linux:**
        ```bash
        source .venv/bin/activate
        ```

3.  **Instalando as Dependências**
    
    ```bash
    pip install -r requirements.txt
    ```

4.  **Iniciando o Dashboard**
    
    ```bash
    streamlit run src/app.py
    ```

---

### 🧑‍💻 Equipe de Desenvolvimento

* **Leticia Braz Bonfim** - [leticia.bonfim@academico.ufpb.br](mailto:leticia.bonfim@academico.ufpb.br) - [GitHub](https://github.com/Leticiabraz)
* **Bianca Lavine da Silva Beserra** - [bianca.lavine@academico.ufpb.br](mailto:bianca.lavine@academico.ufpb.br) - [GitHub](https://github.com/lavine0524)
* **Kaio Vitor Martins** - [kvms@academico.ufpb.br](mailto:kvms@academico.ufpb.br) - [GitHub](https://github.com/kaiov63)
````

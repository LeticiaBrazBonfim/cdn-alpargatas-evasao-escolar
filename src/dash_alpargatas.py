import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import altair as alt


@st.cache_data
def carregar_dados():
    '''
    Carrega o DataFrame completo e cria as colunas de segmentação.
    '''
    ROOT_DIR = Path(__file__).resolve().parent.parent
    DATA_FILE = ROOT_DIR / 'data' / 'processed' / 'data_final_consolidado.parquet'
    try:
        df = pd.read_parquet(DATA_FILE)
    except FileNotFoundError:
        st.error(f"ERRO: O arquivo de dados '{DATA_FILE.name}' não foi encontrado.")
        st.info("Por favor, execute o pipeline de dados primeiro rodando o comando: python src/main.py no terminal")
        return None
    
    # Converte 'ano' para inteiro para garantir a consistência
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce').dropna().astype(int)

    # Segmentação
    df['tem_projeto_ia'] = np.where(
        df['nr_projetos'].notna() & (df['nr_projetos'] > 0), 'Sim', 'Não')
    try:
        df['categoria_pib'] = pd.qcut(df['pib_per_capita'], q=4, labels=[
                                      'Baixo', 'Médio-Baixo', 'Médio-Alto', 'Alto'])
    except Exception:
        df['categoria_pib'] = 'N/A'
    condicoes_porte = [
        (df['populacao'] <= 20000),
        (df['populacao'] > 20000) & (df['populacao'] <= 100000),
        (df['populacao'] > 100000)
    ]
    opcoes_porte = ['Pequeno', 'Médio', 'Grande']
    df['porte_municipio'] = np.select(
        condicoes_porte, opcoes_porte, default='N/A')
    return df

# FUNÇÕES DE VISUALIZAÇÃO


def plot_ideb_por_pib(df_filtrado, ano):
    analise_pib_ideb = df_filtrado.groupby(['categoria_pib', 'tem_projeto_ia'])[
        'ideb_nota'].mean().unstack()
    df_para_plot = analise_pib_ideb.reset_index().melt(
        id_vars='categoria_pib', var_name='tem_projeto_ia', value_name='ideb_nota')
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=df_para_plot, x='categoria_pib', y='ideb_nota',
                hue='tem_projeto_ia', palette='viridis', ax=ax)
    ax.set_title(f'IDEB Médio por Categoria de PIB ({ano})', fontsize=14)
    ax.set_xlabel('Categoria de Riqueza do Município', fontsize=10)
    ax.set_ylabel('Nota Média do IDEB', fontsize=10)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(title='Tem Projeto IA?')
    return fig


# CORPO PRINCIPAL DO DASHBOARD
st.set_page_config(
    layout="wide", page_title="Análise de Atuação Social | Instituto Alpargatas", page_icon="📊")
data_final = carregar_dados()

if data_final is None or data_final.empty:
    st.stop()

# BARRA LATERAL DE NAVEGAÇÃO
st.sidebar.image(
    "https://institutoalpargatas.com.br/wp-content/uploads/2023/10/instituto-alpargatas-logo.svg", width=200)
st.sidebar.title("Páginas de Análise")
pagina_selecionada = st.sidebar.radio(
    "Escolha uma análise:",
    ('Análise de Atuação do Instituto',
     'Análise Socioeconômica (PIB x IDEB)', 'Evolução Histórica do IDEB')
)

# PÁGINA 1: ANÁLISE DE ATUAÇÃO DO INSTITUTO (2020-2021)
if pagina_selecionada == 'Análise de Atuação do Instituto':
    st.title("Análise Estratégica de Atuação do Instituto Alpargatas")
    st.markdown("Esta análise foca em entender o perfil dos municípios onde o Instituto atua, **utilizando dados de 2020 e 2021**, período com cobertura completa de todas as fontes de dados (Projetos IA, PIB e IDEB).")

    # Filtros para esta página
    ano_selecionado = st.sidebar.selectbox(
        'Selecione o Ano para Análise', [2020, 2021], index=1)

    # Filtro de Estado
    estados_disponiveis = sorted(data_final['nome_uf'].dropna().unique())
    estado_selecionado = st.sidebar.selectbox(
        'Selecione o Estado (UF)', ['Todos'] + estados_disponiveis)

    # Filtragem dos dados para esta análise específica
    df_filtrado = data_final[data_final['ano'] == ano_selecionado]
    if estado_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['nome_uf'] == estado_selecionado]

    st.markdown(
        f"Análise para o ano de **{ano_selecionado}** no estado de **{estado_selecionado}**")
    st.markdown("---")

    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para os filtros selecionados.")
    else:
        # Métricas, Gráficos e Tabela...
        col1, col2, col3 = st.columns(3)
        df_com_projeto = df_filtrado[df_filtrado['tem_projeto_ia'] == 'Sim']
        df_sem_projeto = df_filtrado[df_filtrado['tem_projeto_ia'] == 'Não']
        with col1:
            st.metric(label="Municípios com Projetos IA",
                      value=df_com_projeto['id_municipio'].nunique())
        with col2:
            st.metric(label="IDEB Médio (com projetos)",
                      value=f"{df_com_projeto['ideb_nota'].mean():.2f}")
        with col3:
            st.metric(label="IDEB Médio (sem projetos)", value=f"{df_sem_projeto['ideb_nota'].mean():.2f}",
                      delta=f"{(df_com_projeto['ideb_nota'].mean() - df_sem_projeto['ideb_nota'].mean()):.2f}", delta_color="inverse")

        st.markdown("---")
        st.subheader("Análise Estratégica: IDEB por Nível de Riqueza")
        st.pyplot(plot_ideb_por_pib(df_filtrado, ano_selecionado))

# PÁGINA 2: ANÁLISE SOCIOECONÔMICA (2010-2021)
elif pagina_selecionada == 'Análise Socioeconômica (PIB x IDEB)':
    st.title("Análise Socioeconômica: Correlação entre Riqueza e Educação")
    st.markdown("Explore a relação entre o PIB per capita e a nota do IDEB nos municípios. Esta análise utiliza dados do período de **2010 a 2021**.")

    # Filtros para esta página
    df_analise_socio = data_final[data_final['ano'].between(
        2010, 2021)].dropna(subset=['pib_per_capita', 'ideb_nota'])
    anos_disponiveis_socio = sorted(df_analise_socio['ano'].unique())
    ano_selecionado_socio = st.sidebar.selectbox(
        'Selecione o Ano', anos_disponiveis_socio, index=len(anos_disponiveis_socio)-1)

    df_filtrado_socio = df_analise_socio[df_analise_socio['ano']
                                         == ano_selecionado_socio]

    # Gráfico de Dispersão
    st.subheader(f"Contexto: PIB vs. IDEB em {ano_selecionado_socio}")
    fig_pib_ideb = alt.Chart(df_filtrado_socio).mark_circle(size=60).encode(
        x=alt.X('pib_per_capita:Q', title='PIB per Capita (R$)',
                scale=alt.Scale(type="log")),
        y=alt.Y('ideb_nota:Q', title='Nota do IDEB',
                scale=alt.Scale(zero=False)),
        color=alt.Color('regiao:N', title='Região'),
        tooltip=['nome_municipio_formatado', 'pib_per_capita', 'ideb_nota']
    ).properties(height=500).interactive()
    st.altair_chart(fig_pib_ideb, use_container_width=True)


# PÁGINA 3: EVOLUÇÃO HISTÓRICA DO IDEB (2005-2023)
elif pagina_selecionada == 'Evolução Histórica do IDEB':
    st.title("Análise de Evolução Temporal do IDEB")
    st.markdown("Acompanhe a trajetória da nota do IDEB ao longo do tempo para municípios específicos. Esta análise utiliza todos os dados de IDEB disponíveis, de **2005 a 2023**.")

    # Filtros para esta página
    df_analise_ideb = data_final.dropna(subset=['ideb_nota'])
    lista_municipios = sorted(
        df_analise_ideb['nome_municipio_formatado'].unique())
    municipios_selecionados = st.sidebar.multiselect(
        'Selecione os Municípios', lista_municipios, default=lista_municipios[:2] if len(lista_municipios) > 1 else lista_municipios)

    if not municipios_selecionados:
        st.warning("Por favor, selecione ao menos um município na barra lateral.")
    else:
        df_comp = df_analise_ideb[df_analise_ideb['nome_municipio_formatado'].isin(
            municipios_selecionados)]

        # Gráfico de Linha com Altair
        st.header("Evolução Comparativa do IDEB")
        chart = alt.Chart(df_comp).mark_line(point=True).encode(
            x=alt.X('ano:O', title='Ano'),
            y=alt.Y('ideb_nota:Q', title='IDEB', scale=alt.Scale(zero=False)),
            color='nome_municipio_formatado:N',
            tooltip=['nome_municipio_formatado', 'ano', 'ideb_nota']
        ).properties(height=400).interactive()
        st.altair_chart(chart, use_container_width=True)
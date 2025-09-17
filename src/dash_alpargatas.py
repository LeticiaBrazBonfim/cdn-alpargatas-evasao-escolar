import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import altair as alt
from streamlit_option_menu import option_menu

# --- Configuração da Página ---
# Usando layout "wide" para melhor aproveitamento do espaço em dashboards
st.set_page_config(
    page_title="Dashboard | Instituto Alpargatas",
    page_icon="https://yt3.googleusercontent.com/ytc/AIdro_l4A_1O6jESHWd6KEP2atSb8id424a63q2EVFeNkxr-bQ=s900-c-k-c0x00ffffff-no-rj",
    layout="wide"
)

st.markdown("""
<style>
    /* Altera a cor de fundo do tag (o rótulo) */
    div[data-baseweb="tag"] {
        background-color: #ff6a00 !important; 
    }

    /* Altera a cor do texto e do ícone do tag */
    div[data-baseweb="tag"] span, div[data-baseweb="tag"] svg {
        color: white !important;
        fill: white !important;
    }
    
    /* Centraliza a imagem no div com o id 'logo-container' */
    #logo-container {
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)


# --- Carregamento e Cache dos Dados ---
@st.cache_data
def carregar_dados():
    '''
    Carrega o DataFrame completo e cria as colunas de segmentação.
    '''
    # Este caminho pode precisar de ajuste dependendo da estrutura de pastas
    # do seu novo projeto. Assumindo que o app.py está na pasta 'src/app/'.
    try:
        ROOT_DIR = Path(__file__).resolve().parent.parent
        DATA_FILE = ROOT_DIR / 'data' / 'processed' / 'data_final_consolidado.parquet'
        df = pd.read_parquet(DATA_FILE)
    except Exception as e:
        st.error(
            f"ERRO: Não foi possível carregar o arquivo de dados. Verifique o caminho.")
        st.info(f"Detalhe do erro: {e}")
        st.info("Por favor, garanta que o arquivo 'data_final_consolidado.parquet' exista e o caminho esteja correto.")
        return None

    # Processamento e segmentação (mantido do seu código original)
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce').dropna().astype(int)
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

# --- Funções de Plotagem (mantidas do seu código original) ---


def plot_ideb_por_pib(df_filtrado, ano):
    analise_pib_ideb = df_filtrado.groupby(['categoria_pib', 'tem_projeto_ia'])[
        'ideb_nota'].mean().unstack()
    df_para_plot = analise_pib_ideb.reset_index().melt(
        id_vars='categoria_pib', var_name='tem_projeto_ia', value_name='ideb_nota')
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=df_para_plot, x='categoria_pib', y='ideb_nota',
                hue='tem_projeto_ia', palette='viridis', ax=ax)
    ax.set_title(f'IDEB Médio por Categoria de Riqueza ({ano})', fontsize=16)
    ax.set_xlabel('Categoria de Riqueza do Município', fontsize=12)
    ax.set_ylabel('Nota Média do IDEB', fontsize=12)
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.legend(title='Tem Projeto IA?')
    st.pyplot(fig)


# --- Carregamento Inicial ---
df_completo = carregar_dados()

if df_completo is None:
    st.stop()

# --- BARRA LATERAL (SIDEBAR) ---
with st.sidebar:
    st.markdown("<div id='logo-container'>", unsafe_allow_html=True)
    st.image(
        "https://cdn.v2v.net/70fe53dd-da8c-48e8-8525-6e829825e319.png?v=63802404261", width=200)
    st.markdown("</div>", unsafe_allow_html=True)

    pagina_selecionada = option_menu(
        "Menu Principal",
        options=['Análise de Atuação',
                 'Análise Socioeconômica', 'Evolução Histórica'],
        icons=['clipboard-data', 'graph-up-arrow', 'bar-chart-line'],
        menu_icon="cast", default_index=0,
        styles={ 
            "container": {"background-color": "#fafafa"},
            "icon": {"color": "cinza", "font-size": "20px"},
            "nav-link": {"font-size": "16px", "text-align": "left", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#ff6a00ff"},
        }
    )

    st.sidebar.header("Filtros")

# --- LÓGICA DAS PÁGINAS ---

# PÁGINA 1: Análise de Atuação do Instituto
if pagina_selecionada == 'Análise de Atuação':
    st.title("📊 Análise Estratégica de Atuação do Instituto Alpargatas")
    st.markdown("Esta análise foca em entender o perfil dos municípios onde o Instituto atua, **utilizando dados de 2020 a 2023**, período com cobertura completa de todas as fontes de dados.")

    # Filtros movidos para a sidebar
    ano_selecionado = st.sidebar.selectbox(
        'Selecione o Ano', [2021, 2023], index=1, key='ano_atuacao')
    estados_disponiveis = sorted(df_completo['nome_uf'].dropna().unique())
    estado_selecionado = st.sidebar.selectbox('Selecione o Estado (UF)', [
                                            'Todos'] + estados_disponiveis, key='estado_atuacao')

    # Filtragem dos dados
    df_filtrado = df_completo[df_completo['ano'] == ano_selecionado]
    if estado_selecionado != 'Todos':
        df_filtrado = df_filtrado[df_filtrado['nome_uf'] == estado_selecionado]

    st.markdown(
        f"#### Análise para o ano de **{ano_selecionado}** no estado de **{estado_selecionado}**")
    st.divider()

    if df_filtrado.empty:
        st.warning("Não há dados disponíveis para os filtros selecionados.")
    else:
        # Métricas
        col1, col2, col3 = st.columns(3)
        df_com_projeto = df_filtrado[df_filtrado['tem_projeto_ia'] == 'Sim']
        df_sem_projeto = df_filtrado[df_filtrado['tem_projeto_ia'] == 'Não']

        col1.metric("Municípios com Projetos IA",
                    df_com_projeto['id_municipio'].nunique())
        col2.metric("IDEB Médio (com projetos)",
                    f"{df_com_projeto['ideb_nota'].mean():.2f}")
        delta_ideb = df_com_projeto['ideb_nota'].mean(
        ) - df_sem_projeto['ideb_nota'].mean()
        col3.metric("IDEB Médio (sem projetos)",
                    f"{df_sem_projeto['ideb_nota'].mean():.2f}", delta=f"{delta_ideb:.2f}", delta_color="normal")

        st.divider()

        # Gráfico
        st.subheader("Análise Estratégica: IDEB por Nível de Riqueza")
        with st.container(border=True):
            plot_ideb_por_pib(df_filtrado, ano_selecionado)
            
        st.divider()
        st.info("ℹ️ Nota sobre os dados: O Produto Interno Bruto (PIB) para o ano de 20223 é uma estimativa baseada na replicação dos valores do último ano disponível (2021).")


# PÁGINA 2: Análise Socioeconômica (PIB x IDEB)
elif pagina_selecionada == 'Análise Socioeconômica':
    st.title("📈 Análise Socioeconômica: Correlação entre Riqueza e Educação")
    st.markdown("Explore a relação entre o PIB per capita e a nota do IDEB nos municípios. Esta análise utiliza dados do período de **2010 a 2021**.")

    # Filtros movidos para a sidebar
    df_analise_socio = df_completo[df_completo['ano'].between(
        2010, 2021)].dropna(subset=['pib_per_capita', 'ideb_nota'])
    anos_disponiveis_socio = sorted(df_analise_socio['ano'].unique())
    ano_selecionado_socio = st.sidebar.selectbox(
        'Selecione o Ano', anos_disponiveis_socio, index=len(anos_disponiveis_socio)-1, key='ano_socio')

    # Filtragem e Gráfico
    df_filtrado_socio = df_analise_socio[df_analise_socio['ano']
                                         == ano_selecionado_socio]

    st.subheader(f"Contexto: PIB vs. IDEB em {ano_selecionado_socio}")
    with st.container(border=True):
        scatter_chart = alt.Chart(df_filtrado_socio).mark_circle(size=80, opacity=0.7).encode(
            x=alt.X('pib_per_capita:Q', title='PIB per Capita (R$)',
                    scale=alt.Scale(type="log")),
            y=alt.Y('ideb_nota:Q', title='Nota do IDEB',
                    scale=alt.Scale(zero=False)),
            color=alt.Color('regiao:N', title='Região'),
            tooltip=['nome_municipio_formatado', 'pib_per_capita', 'ideb_nota']
        ).properties(height=500).interactive()
        st.altair_chart(scatter_chart, use_container_width=True)

# PÁGINA 3: Evolução Histórica do IDEB
elif pagina_selecionada == 'Evolução Histórica':
    st.title("📉 Análise de Evolução Temporal do IDEB")
    st.markdown("Acompanhe a trajetória da nota do IDEB ao longo do tempo para municípios específicos. Esta análise utiliza todos os dados de IDEB disponíveis, de **2005 a 2023**.")

    # Filtros movidos para a sidebar
    df_analise_ideb = df_completo.dropna(subset=['ideb_nota'])
    lista_municipios = sorted(
        df_analise_ideb['nome_municipio_formatado'].unique())
    default_selection = lista_municipios[:3] if len(
        lista_municipios) > 2 else lista_municipios
    municipios_selecionados = st.sidebar.multiselect(
        'Selecione os Municípios', lista_municipios, default=default_selection, key='municipios_evolucao')

    # Gráfico
    if not municipios_selecionados:
        st.warning("Por favor, selecione ao menos um município na barra lateral.")
    else:
        df_comp = df_analise_ideb[df_analise_ideb['nome_municipio_formatado'].isin(
            municipios_selecionados)]

        st.header("Evolução Comparativa do IDEB")
        with st.container(border=True):
            line_chart = alt.Chart(df_comp).mark_line(point=True).encode(
                x=alt.X('ano:O', title='Ano'),
                y=alt.Y('ideb_nota:Q', title='IDEB',
                        scale=alt.Scale(zero=False)),
                color=alt.Color('nome_municipio_formatado:N',
                                title='Município'),
                tooltip=['nome_municipio_formatado', 'ano', 'ideb_nota']
            ).properties(height=500).interactive()
            st.altair_chart(line_chart, use_container_width=True)

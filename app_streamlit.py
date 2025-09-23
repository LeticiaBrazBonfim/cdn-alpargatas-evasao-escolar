import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import numpy as np
from pathlib import Path
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Instituto Alpargatas",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- TAREFA 1: CSS CUSTOMIZADO PARA O BOTÃO ---
# Injeta CSS para estilizar o botão de download
st.markdown("""
<style>
    /* Alvo é a div que contém o botão de download */
    div.stDownloadButton > button {
        background-color: #ff6a00; /* Cor de fundo laranja */
        color: white;              /* Cor do texto branca */
        border: 2px solid #ff6a00; /* Borda laranja */
        border-radius: 5px;      /* Bordas arredondadas */
    }
    /* Efeito ao passar o mouse */
    div.stDownloadButton > button:hover {
        background-color: white;
        color: #ff6a00;
        border: 2px solid #ff6a00;
    }
</style>
""", unsafe_allow_html=True)


# --- CARREGAMENTO E CACHE DOS DADOS ---
@st.cache_data
def carregar_dados():
    """Lê os dados processados e os enriquece com dados categóricos para os filtros."""
    script_path = Path(__file__).resolve().parent
    root_dir = script_path if (
        script_path / 'data').exists() else script_path.parent

    DATA_FILE = root_dir / 'data' / 'processed' / 'data_final_consolidado.parquet'
    GEO_FILE = root_dir / 'data' / 'raw' / 'municipios.csv'

    try:
        df = pd.read_parquet(DATA_FILE)
        df_geo = pd.read_csv(GEO_FILE)
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar arquivos de dados: {e}")
        st.info("Verifique se os arquivos 'data_final_consolidado.parquet' e 'municipios.csv' estão nos locais corretos.")
        return None

    # Merge com dados geográficos
    df = df.merge(df_geo[['codigo_ibge', 'latitude', 'longitude']],
                  left_on='id_municipio', right_on='codigo_ibge', how='left')

    # Limpeza e formatação de colunas
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
    df['tem_projeto'] = df['nr_projetos'].fillna(0) > 0
    df['status_projeto'] = df['tem_projeto'].map(
        {True: 'Com Projetos', False: 'Sem Projetos'})

    # --- CRIAÇÃO DAS COLUNAS CATEGÓRICAS PARA OS FILTROS DA ANÁLISE DE IMPACTO ---
    # Cria faixas de População
    df['faixa_populacao'] = pd.qcut(df['populacao'], q=4, labels=[
        'População Baixa', 'População Média-Baixa', 'População Média-Alta', 'População Alta'], duplicates='drop')

    # Cria faixas de PIB
    if 'pib_mil_reais' in df.columns:
        df['faixa_pib'] = pd.qcut(df['pib_mil_reais'], q=4, labels=[
            'PIB Baixo', 'PIB Médio-Baixo', 'PIB Médio-Alto', 'PIB Alto'], duplicates='drop')

    # Cria faixas de PIB per Capita
    if 'pib_per_capita' in df.columns:
        df['faixa_pib_per_capita'] = pd.qcut(df['pib_per_capita'], q=4, labels=[
            'PIB per Capita Baixo', 'PIB per Capita Médio-Baixo', 'PIB per Capita Médio-Alto', 'PIB per Capita Alto'], duplicates='drop')

    return df


# --- FUNÇÃO PRINCIPAL DO DASHBOARD ---
def construir_dashboard(df_completo):

    st.title("Dashboard Estratégico - Instituto Alpargatas")

    # --- NAVEGAÇÃO ---
    aba_selecionada = option_menu(
        menu_title=None,
        options=["Visão Geral", "Análise Geográfica", "Análise de Impacto",
                 "Análise de Correlação", "Dados Detalhados"],
        icons=["bar-chart-line", "map", "bullseye", "bezier", "table"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"border-bottom": "2px solid #eee", "padding": "0 !important", "margin": "0 !important"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": "#ff6a00", "color": "white"},
        }
    )

    # --- SIDEBAR DE FILTROS ---
    with st.sidebar:
        st.image(
            "https://cdn.v2v.net/70fe53dd-da8c-48e8-8525-6e829825e319.png?v=63802404261", width=200)
        st.title("Filtros de Análise")
        ano_selecionado = st.selectbox("Ano de Análise", sorted(
            df_completo['ano'].dropna().unique(), reverse=True))
        estados_disponiveis = sorted(df_completo['sg_uf'].dropna().unique())
        estados_selecionados = st.multiselect(
            "Estados (UF)", options=estados_disponiveis, default=estados_disponiveis)

    # Filtra os dados com base na seleção da sidebar
    df_filtrado = df_completo[(df_completo['ano'] == ano_selecionado) & (
        df_completo['sg_uf'].isin(estados_selecionados))]

    # --- LÓGICA DE EXIBIÇÃO DAS ABAS ---
    if aba_selecionada == "Visão Geral":
        st.header(f"Resumo do Ano de {ano_selecionado}")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Municípios Analisados",
                    df_filtrado['id_municipio'].nunique())
        col2.metric("Projetos Ativos", int(df_filtrado['nr_projetos'].sum()))
        col3.metric("Estudantes Beneficiados", int(
            df_filtrado['nr_beneficiados'].sum()))
        col4.metric("IDEB Médio (Público)",
                    f"{df_filtrado['ideb_nota'].mean():.2f}")

    elif aba_selecionada == "Análise Geográfica":
        st.header("Mapa de Atuação do Instituto")
        df_mapa = df_filtrado[['latitude', 'longitude', 'nome_municipio_formatado', 'tem_projeto']].copy(
        ).dropna(subset=['latitude', 'longitude'])
        df_mapa['cor'] = df_mapa['tem_projeto'].apply(
            lambda x: [255, 106, 0] if x else [200, 200, 200, 100])
        st.pydeck_chart(pdk.Deck(
            map_style='mapbox://styles/mapbox/light-v9',
            initial_view_state=pdk.ViewState(
                latitude=-14.2350, longitude=-51.9253, zoom=3, pitch=0),
            layers=[pdk.Layer('ScatterplotLayer', data=df_mapa, get_position='[longitude, latitude]',
                              get_color='cor', get_radius=15000, pickable=True)],

            tooltip={"text": "{nome_municipio_formatado}\nAtuação: {tem_projeto}"} # type: ignore
        ))
        st.caption(
            "Municípios em laranja indicam atuação do Instituto Alpargatas.")

    elif aba_selecionada == "Análise de Impacto":
        st.header("Análise de Impacto")
        st.markdown(
            "Análise comparativa dos resultados educacionais por agrupamento de municípios.")

        indicadores = {
            "Nota IDEB": "ideb_nota",
            "Taxa de Distorção Idade-Série": "taxa_distorcao_total_fun",
        }
        segmentacoes = {
            "PIB": "faixa_pib",
            "PIB per Capita": "faixa_pib_per_capita",
            "População": "faixa_populacao",
        }

        col1, col2 = st.columns(2)
        indicador_nome = col1.selectbox(
            "Indicador para Análise:", options=list(indicadores.keys()))
        segmentacao_nome = col2.selectbox(
            "Agrupar Municípios por:", options=list(segmentacoes.keys()))

        indicador_id = indicadores[indicador_nome]
        segmentacao_id = segmentacoes[segmentacao_nome]

        if segmentacao_id in df_completo.columns and indicador_id in df_completo.columns:
            df_impacto = df_completo.groupby([segmentacao_id, 'status_projeto']).agg(
                valor_medio=(indicador_id, 'mean')).reset_index()

            chart = alt.Chart(df_impacto).mark_bar().encode(
                x=alt.X(f'{segmentacao_id}:N',
                        title=segmentacao_nome,
                        sort=None,
                        axis=alt.Axis(labelAngle=0)
                        ),
                y=alt.Y('valor_medio:Q', title=f"Média de {indicador_nome}"),
                color=alt.Color('status_projeto:N', title="Status", scale=alt.Scale(
                    domain=['Com Projetos', 'Sem Projetos'],
                    range=['#ff6a00', '#cccccc'])
                ),
                xOffset='status_projeto:N',
                tooltip=[alt.Tooltip(segmentacao_id, title=segmentacao_nome),
                         alt.Tooltip('status_projeto', title='Status'),
                         alt.Tooltip('valor_medio', title='Valor Médio', format='.2f')]
            ).properties(height=500)
            st.altair_chart(chart, use_container_width=True)
        else:
            st.warning(
                f"A(s) coluna(s) para a análise ('{segmentacao_id}' ou '{indicador_id}') não foi/foram encontrada(s) no DataFrame.")

    elif aba_selecionada == "Análise de Correlação":
        st.header("Análise de Correlação: Fatores Socioeconômicos e Educacionais")
        colunas_interesse = ['ideb_nota', 'pib_per_capita', 'populacao',
                             'taxa_distorcao_total_fun', 'nr_projetos', 'nr_beneficiados']
        col1, col2 = st.columns(2)
        eixo_x = col1.selectbox("Eixo X", colunas_interesse, index=1)
        eixo_y = col2.selectbox("Eixo Y", colunas_interesse, index=0)

        df_corr = df_filtrado.dropna(subset=[eixo_x, eixo_y])
        scatter_chart = alt.Chart(df_corr).mark_circle(size=60, opacity=0.7).encode(
            x=alt.X(eixo_x, title=eixo_x.replace('_', ' ').title()),
            y=alt.Y(eixo_y, title=eixo_y.replace('_', ' ').title()),
            tooltip=['nome_municipio_formatado', eixo_x, eixo_y]
        ).properties(height=500).interactive()
        st.altair_chart(scatter_chart, use_container_width=True)

    elif aba_selecionada == "Dados Detalhados":
        st.header("Dados Detalhados dos Municípios")
        busca = st.text_input("Buscar município ou estado...")
        df_tabela = df_filtrado
        if busca:
            df_tabela = df_filtrado[df_filtrado['nome_municipio_formatado'].str.contains(
                busca, case=False) | df_filtrado['sg_uf'].str.contains(busca, case=False)]

        st.dataframe(df_tabela[['nome_municipio_formatado', 'sg_uf', 'populacao', 'ideb_nota', 'pib_per_capita',
                     'nr_projetos', 'nr_beneficiados', 'taxa_distorcao_total_fun']], use_container_width=True)

        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        # O botão abaixo será estilizado pelo CSS injetado no início do script
        st.download_button(label="Exportar para CSV", data=convert_df_to_csv(
            df_tabela), file_name=f'dados_detalhados_{ano_selecionado}.csv', mime='text/csv')

    # --- TAREFA 2: RODAPÉ COM FUNDO LARANJA ---
    st.divider()
    desenvolvedores = "Leticia Braz Bonfim, Bianca Lavine da Silva Beserra, Kaio Vitor Martins"
    ano = 2025
    st.markdown(
        f'<div style="background-color: #ff6a00; padding: 10px; border-radius: 5px; text-align: center; color: white; font-size: 14px;"><p style="margin:0;"><b>Desenvolvedores:</b> {desenvolvedores} | <b>Ano:</b> {ano}</p><p style="margin:0;">Projeto de Extensão da UFPB | Curso: Ciência de Dados para Negócios | Disciplina: Análise de Dados.</p></div>', unsafe_allow_html=True)


# --- PONTO DE ENTRADA PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    df_principal = carregar_dados()
    if df_principal is not None:
        construir_dashboard(df_principal)

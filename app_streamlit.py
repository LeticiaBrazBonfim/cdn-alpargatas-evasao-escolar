import streamlit as st
import pandas as pd
import altair as alt
import pydeck as pdk
import numpy as np
import json
import plotly.express as px
from pathlib import Path
from streamlit_option_menu import option_menu

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(
    page_title="Dashboard Instituto Alpargatas",
    page_icon="👟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- DEFINIÇÃO DA COR LARANJA ---
COR_LARANJA = "#ff6a00"

# --- CSS CUSTOMIZADO ---
st.markdown(f"""
<style>
    /* Alvo é a div que contém o botão de download */
    div.stDownloadButton > button {{
        background-color: {COR_LARANJA};
        color: white;
        border: 2px solid {COR_LARANJA};
        border-radius: 5px;
    }}
    /* Efeito ao passar o mouse */
    div.stDownloadButton > button:hover {{
        background-color: white;
        color: {COR_LARANJA};
        border: 2px solid {COR_LARANJA};
    }}
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

    # CRIAÇÃO DAS COLUNAS CATEGÓRICAS PARA OS FILTROS DA ANÁLISE DE IMPACTO
    df['faixa_populacao'] = pd.qcut(df['populacao'], q=4, labels=[
        'População Baixa', 'População Média-Baixa', 'População Média-Alta', 'População Alta'], duplicates='drop')
    if 'pib_mil_reais' in df.columns:
        df['faixa_pib'] = pd.qcut(df['pib_mil_reais'], q=4, labels=[
            'PIB Baixo', 'PIB Médio-Baixo', 'PIB Médio-Alto', 'PIB Alto'], duplicates='drop')
    if 'pib_per_capita' in df.columns:
        df['faixa_pib_per_capita'] = pd.qcut(df['pib_per_capita'], q=4, labels=[
            'PIB per Capita Baixo', 'PIB per Capita Médio-Baixo', 'PIB per Capita Médio-Alto', 'PIB per Capita Alto'], duplicates='drop')

    return df


@st.cache_data
def carregar_geojson():
    # le aquivo json
    script_path = Path(__file__).resolve().parent
    root_dir = script_path if (
        script_path / 'data').exists() else script_path.parent

    GEOJSON_FILE = root_dir / 'data' / 'raw' / 'brasil_municipios.json'

    try:
        with open(GEOJSON_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(
            f"ARQUIVO DO MAPA NÃO ENCONTRADO: Verifique se o arquivo '{GEOJSON_FILE.name}' está na pasta '{GEOJSON_FILE.parent}'.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro ao ler o arquivo GeoJSON: {e}")
        return None


# --- FUNÇÃO PRINCIPAL DO DASHBOARD ---
def construir_dashboard(df_completo):

    st.title("Dashboard Estratégico - Instituto Alpargatas")

    # --- NAVEGAÇÃO ---
    aba_selecionada = option_menu(
        menu_title=None,
        options=["Visão Geral", "Análise Geográfica", "Análise de Impacto",
                 "Análise Histórica", "Análise de Correlação", "Dados Detalhados"],
        icons=["bar-chart-line", "map", "bullseye",
               "graph-up", "bezier", "table"],
        menu_icon="cast",
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"border-bottom": "2px solid #eee", "padding": "0 !important", "margin": "0 !important"},
            "nav-link": {"font-size": "16px", "text-align": "center", "margin": "0px", "--hover-color": "#eee"},
            "nav-link-selected": {"background-color": COR_LARANJA, "color": "white"},
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

        # KPI 1: Municípios com contexto
        total_municipios = df_filtrado['id_municipio'].nunique()
        col1.metric("Municípios Analisados", total_municipios)
        status_counts = df_filtrado['status_projeto'].value_counts()
        com_projetos = status_counts.get('Com Projetos', 0)
        sem_projetos = status_counts.get('Sem Projetos', 0)
        col1.markdown(
            f"<small><b><span style='color:{COR_LARANJA};'>{com_projetos}</span></b> com projetos | <b><span style='color:{COR_LARANJA};'>{sem_projetos}</span></b> sem projetos</small>", unsafe_allow_html=True)

        # KPI 2: Projetos
        col2.metric("Projetos Ativos", int(df_filtrado['nr_projetos'].sum()))

        # KPI 3: Beneficiados
        col3.metric("Estudantes Beneficiados", int(
            df_filtrado['nr_beneficiados'].sum()))

        # KPI 4: IDEB Médio com contexto
        ideb_medio = df_filtrado['ideb_nota'].mean()
        col4.metric("IDEB Médio (Público)", f"{ideb_medio:.2f}")
        ideb_min = df_filtrado['ideb_nota'].min()
        ideb_max = df_filtrado['ideb_nota'].max()
        col4.markdown(
            f"<small>Mínimo: <b><span style='color:{COR_LARANJA};'>{ideb_min:.2f}</span></b> | Máximo: <b><span style='color:{COR_LARANJA};'>{ideb_max:.2f}</span></b></small>", unsafe_allow_html=True)

        st.divider()

        # Ranking de Municípios
        st.subheader("Rankings Municipais")
        indicador_ranking = st.selectbox("Analisar por:", [
                                         "IDEB (maior para menor)", "Taxa de Distorção (menor para maior)"])

        if indicador_ranking == "IDEB (maior para menor)":
            df_rank = df_filtrado.sort_values(
                by='ideb_nota', ascending=False).dropna(subset=['ideb_nota'])
        else:
            df_rank = df_filtrado.sort_values(by='taxa_distorcao_total_fun', ascending=True).dropna(
                subset=['taxa_distorcao_total_fun'])

        col_rank1, col_rank2 = st.columns(2)
        col_rank1.write("**🏆 Top 5 Melhores Resultados**")
        col_rank1.dataframe(df_rank[['nome_municipio_formatado', 'ideb_nota',
                            'taxa_distorcao_total_fun']].head(5), use_container_width=True)

        col_rank2.write("**⚠️ 5 Maiores Desafios**")
        col_rank2.dataframe(df_rank[['nome_municipio_formatado', 'ideb_nota', 'taxa_distorcao_total_fun']].tail(
            5).sort_values(by='taxa_distorcao_total_fun', ascending=False), use_container_width=True)

    elif aba_selecionada == "Análise Geográfica":
        st.header("Mapa de Atuação e Análise Municipal")
        st.markdown(
            "Passe o mouse sobre um município para ver detalhes. Use os filtros na barra lateral para focar em um estado específico.")

        if df_filtrado.empty:
            st.warning("Nenhum dado disponível para os filtros selecionados.")
        else:
            geojson_data = carregar_geojson()

            if geojson_data:
                df_mapa = df_filtrado.copy()
                df_mapa['id_municipio'] = df_mapa['id_municipio'].astype(str)

                # logica zoom
                map_zoom = 3
                map_center = {"lat": -14.2350, "lon": -51.9253}

                # se apenas um estado for selecionado no filtro, ajusta o zoom
                if len(estados_selecionados) == 1:
                    df_estado_zoom = df_filtrado.dropna(
                        subset=['latitude', 'longitude'])
                    if not df_estado_zoom.empty:
                        map_center = {
                            "lat": df_estado_zoom['latitude'].mean(),
                            "lon": df_estado_zoom['longitude'].mean()
                        }
                        map_zoom = 6  # Zoom um pouco mais próximo para um estado

                fig = px.choropleth_mapbox(
                    df_mapa,
                    geojson=geojson_data,
                    locations='id_municipio',
                    featureidkey="properties.id",
                    color='status_projeto',
                    color_discrete_map={
                        'Com Projetos': COR_LARANJA,
                        'Sem Projetos': 'rgba(0, 0, 0, 0)'
                    },
                    hover_name='nome_municipio_formatado',
                    hover_data={
                        'sg_uf': True,
                        'nr_projetos': True,
                        'nr_beneficiados': True,
                        'populacao': True,
                        'ideb_nota': ':.2f',
                        'pib_per_capita': ':.2f'
                    },
                    mapbox_style="carto-positron",
                    zoom=map_zoom,
                    center=map_center,
                    opacity=0.8
                )

                fig.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    legend_title_text='Status de Atuação'
                )

                st.plotly_chart(fig, use_container_width=True)

    elif aba_selecionada == "Análise de Impacto":
        st.header("Análise Comparativa de Indicadores")
        st.markdown(
            "Compare os resultados educacionais entre grupos de municípios com e sem projetos do Instituto.")

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
                    range=[COR_LARANJA, '#cccccc'])
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

    elif aba_selecionada == "Análise Histórica":
        st.header("Evolução Histórica do Município")
        st.markdown(
            "Acompanhe a tendência de um indicador para um município específico ao longo dos anos.")

        # Filtros da aba
        municipios_disponiveis = sorted(
            df_filtrado['nome_municipio_formatado'].unique())
        indicadores_hist = {"Nota IDEB": "ideb_nota",
                            "Taxa de Distorção Idade-Série": "taxa_distorcao_total_fun"}

        col1, col2 = st.columns(2)
        municipio_selecionado = col1.selectbox(
            "Selecione o Município:", municipios_disponiveis)
        indicador_hist_nome = col2.selectbox(
            "Selecione o Indicador:", list(indicadores_hist.keys()))
        indicador_hist_id = indicadores_hist[indicador_hist_nome]

        if municipio_selecionado:
            df_historico_mun = df_completo[df_completo['nome_municipio_formatado']
                                           == municipio_selecionado].dropna(subset=[indicador_hist_id])

            if not df_historico_mun.empty:
                chart_hist = alt.Chart(df_historico_mun).mark_line(point=True).encode(
                    x=alt.X('ano:O', title='Ano'),
                    y=alt.Y(f'{indicador_hist_id}:Q',
                            title=indicador_hist_nome),
                    color=alt.value(COR_LARANJA),
                    tooltip=[alt.Tooltip('ano', title='Ano'),
                             alt.Tooltip(indicador_hist_id, title='Valor', format='.2f')]
                ).properties(height=500, title=f"Evolução de {indicador_hist_nome} em {municipio_selecionado}")
                st.altair_chart(chart_hist, use_container_width=True)
            else:
                st.info(
                    "Não há dados históricos suficientes para este indicador no município selecionado.")
        else:
            st.info("Selecione um município para visualizar a análise histórica.")

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
            color=alt.value(COR_LARANJA),
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

        st.download_button(label="Exportar para CSV", data=convert_df_to_csv(
            df_tabela), file_name=f'dados_detalhados_{ano_selecionado}.csv', mime='text/csv')

    # RODAPÉ
    st.divider()
    desenvolvedores = "Leticia Braz Bonfim, Bianca Lavine da Silva Beserra, Kaio Vitor Martins"
    ano = 2025
    st.markdown(
        f'<div style="background-color: {COR_LARANJA}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-size: 14px;"><p style="margin:0;"><b>Desenvolvedores:</b> {desenvolvedores} | <b>Ano:</b> {ano}</p><p style="margin:0;">Projeto de Extensão da UFPB | Curso: Ciência de Dados para Negócios | Disciplina: Análise de Dados.</p></div>', unsafe_allow_html=True)


# --- PONTO DE ENTRADA PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    df_principal = carregar_dados()
    if df_principal is not None:
        geojson_principal = carregar_geojson()
        construir_dashboard(df_principal)

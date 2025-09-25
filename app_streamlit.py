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
    page_icon="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTEOAgYSyDDH-4sj9gP9TWvgdadFFmPqyO7oQ&s",
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

    try:
        df = pd.read_parquet(DATA_FILE)
    except FileNotFoundError as e:
        st.error(f"Erro ao carregar arquivo de dados: {e}")
        st.info(
            "Verifique se o arquivo 'data_final_consolidado.parquet' está no local correto.")
        return None

    # Limpeza e formatação de colunas
    df['ano'] = pd.to_numeric(df['ano'], errors='coerce')
    df['tem_projeto'] = df['nr_projetos'].fillna(0) > 0
    df['status_projeto'] = df['tem_projeto'].map(
        {True: 'Com Projetos', False: 'Sem Projetos'})

    # CRIAÇÃO DAS COLUNAS CATEGÓRICAS PARA OS FILTROS DA ANÁLISE DE IMPACTO
    df['faixa_populacao'] = pd.qcut(df['populacao'], q=4, labels=[
        'Pequeno Porte', 'Médio Porte', 'Grande Porte', 'Metrópole'], duplicates='drop')
    if 'pib_mil_reais' in df.columns:
        df['faixa_pib'] = pd.qcut(df['pib_mil_reais'], q=4, labels=[
            'PIB Baixo', 'PIB Médio-Baixo', 'PIB Médio-Alto', 'PIB Alto'], duplicates='drop')
    if 'pib_per_capita' in df.columns:
        df['faixa_pib_per_capita'] = pd.qcut(df['pib_per_capita'], q=4, labels=[
            'PIB per Capita Baixo', 'PIB per Capita Médio-Baixo', 'PIB per Capita Médio-Alto', 'PIB per Capita Alto'], duplicates='drop')

    return df


@st.cache_data
def carregar_geojson():
    """Lê o arquivo GeoJSON com as geometrias dos municípios."""
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

        # --- LÓGICA DO FILTRO DE ANO REVERTIDA ---
        anos_disponiveis = sorted(
            df_completo['ano'].dropna().unique(), reverse=True)
        ano_selecionado = st.selectbox("Ano de Análise", anos_disponiveis)

        # --- LÓGICA DO FILTRO DE ESTADOS COM BOTÃO E STATE MANAGEMENT ---
        estados_disponiveis = sorted(df_completo['sg_uf'].dropna().unique())

        # Inicializa o session_state na primeira execução
        if 'estados_selecionados' not in st.session_state:
            st.session_state.estados_selecionados = estados_disponiveis

        # O multiselect agora usa o session_state como padrão
        selecao_manual = st.multiselect(
            "Estados (UF)",
            options=estados_disponiveis,
            default=st.session_state.estados_selecionados
        )

        # Botão para selecionar tudo, posicionado abaixo do multiselect
        if st.button("Selecionar Tudo", use_container_width=True):
            st.session_state.estados_selecionados = estados_disponiveis
            st.rerun()

        # Sincroniza a seleção manual de volta para o session_state
        if selecao_manual != st.session_state.estados_selecionados:
            st.session_state.estados_selecionados = selecao_manual
            st.rerun()

    # Filtra os dados com base na seleção da sidebar (agora vinda do session_state)
    df_filtrado = df_completo[(df_completo['ano'] == ano_selecionado) & (
        df_completo['sg_uf'].isin(st.session_state.estados_selecionados))]

    # --- LÓGICA DE EXIBIÇÃO DAS ABAS ---
    if aba_selecionada == "Visão Geral":
        st.header(f"Resumo do Ano de {ano_selecionado}")

        if df_filtrado.empty:
            st.warning("Nenhum dado disponível para os filtros selecionados.")
        else:
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
            col2.metric("Projetos Ativos", int(
                df_filtrado['nr_projetos'].sum()))

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

            # --- INÍCIO DA CORREÇÃO ---
            # Adicionando HTML para os ícones Bootstrap. O Streamlit já inclui a folha de estilos necessária.
            col_rank1.markdown(
                '<p style="font-weight: bold;"><i class="bi bi-trophy-fill"></i> Top 5 Melhores Resultados</p>', unsafe_allow_html=True)
            col_rank1.dataframe(df_rank[['nome_municipio_formatado', 'ideb_nota',
                                'taxa_distorcao_total_fun']].head(5), use_container_width=True)

            col_rank2.markdown(
                '<p style="font-weight: bold;"><i class="bi bi-exclamation-triangle-fill"></i> 5 Maiores Desafios</p>', unsafe_allow_html=True)
            col_rank2.dataframe(df_rank[['nome_municipio_formatado', 'ideb_nota', 'taxa_distorcao_total_fun']].tail(
                5).sort_values(by='taxa_distorcao_total_fun', ascending=False), use_container_width=True)
            # --- FIM DA CORREÇÃO ---

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

                fig = px.choropleth_mapbox(
                    df_mapa,
                    geojson=geojson_data,
                    locations='id_municipio',
                    featureidkey="properties.id",
                    color='status_projeto',
                    color_discrete_map={
                        'Com Projetos': COR_LARANJA,
                        'Sem Projetos': 'lightgrey'
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
                    zoom=3,
                    center={"lat": -14.2350, "lon": -51.9253},
                    opacity=0.7
                )

                fig.update_layout(
                    margin={"r": 0, "t": 0, "l": 0, "b": 0},
                    legend_title_text='Status de Atuação'
                )

                st.plotly_chart(fig, use_container_width=True)

    elif aba_selecionada == "Análise de Impacto":
        # Seção de Análise de Evolução
        st.header("Análise da Evolução do Impacto (Comparativo)")
        st.markdown(
            "Compare a evolução de um indicador entre dois anos, para municípios com e sem projetos, segmentado por uma característica.")

        col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)

        indicadores_evolucao = {"Nota IDEB": "ideb_nota",
                                "Taxa de Distorção": "taxa_distorcao_total_fun"}
        indicador_nome_evo = col_sel1.selectbox(
            "Indicador para Análise de Evolução", options=list(indicadores_evolucao.keys()))
        indicador_id_evo = indicadores_evolucao[indicador_nome_evo]

        segmentacoes_evolucao = {"População": "faixa_populacao",
                                 "PIB": "faixa_pib", "PIB per Capita": "faixa_pib_per_capita"}
        segmentacao_nome_evo = col_sel2.selectbox(
            "Agrupar Evolução por", options=list(segmentacoes_evolucao.keys()))
        segmentacao_id_evo = segmentacoes_evolucao[segmentacao_nome_evo]

        anos_validos = sorted(df_completo.dropna(
            subset=[indicador_id_evo])['ano'].unique().astype(int))

        if len(anos_validos) < 2:
            st.warning(
                f"Não há dados suficientes (pelo menos dois anos) para a análise de evolução da '{indicador_nome_evo}'.")
        else:
            ano_inicial = col_sel3.selectbox(
                "Ano Inicial", options=anos_validos, index=0)
            ano_final = col_sel4.selectbox(
                "Ano Final", options=anos_validos, index=len(anos_validos)-1)

            if ano_inicial is not None and ano_final is not None and ano_inicial >= ano_final:
                st.error("O Ano Inicial deve ser anterior ao Ano Final.")
            else:
                df_periodo = df_completo[df_completo['ano'].isin([ano_inicial, ano_final])].dropna(
                    subset=[indicador_id_evo, segmentacao_id_evo])
                if indicador_id_evo == 'ideb_nota':
                    df_agregado = df_periodo.groupby([segmentacao_id_evo, 'ano', 'status_projeto'])[
                        indicador_id_evo].mean().reset_index()
                    if not df_agregado.empty:
                        chart = alt.Chart(df_agregado).mark_bar().encode(x=alt.X('ano:O', title="Ano", axis=alt.Axis(labelAngle=0)), y=alt.Y(f'{indicador_id_evo}:Q', title=f'Média de {indicador_nome_evo}'), color=alt.Color('status_projeto:N', title="Possui Projeto?", scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, '#cccccc'])), xOffset='status_projeto:N', tooltip=[alt.Tooltip(
                            segmentacao_id_evo, title=segmentacao_nome_evo), alt.Tooltip('ano', title='Ano'), alt.Tooltip('status_projeto', title='Status'), alt.Tooltip(indicador_id_evo, title='Valor Médio', format='.2f')]).properties(width=180, height=350).facet(column=alt.Column(f'{segmentacao_id_evo}:N', title=segmentacao_nome_evo, sort=['Pequeno Porte', 'Médio Porte', 'Grande Porte', 'Metrópole']))
                        st.altair_chart(chart)
                elif indicador_id_evo == 'taxa_distorcao_total_fun':
                    df_pivot = df_periodo.pivot_table(
                        index=['id_municipio', segmentacao_id_evo, 'status_projeto'], columns='ano', values=indicador_id_evo).reset_index()
                    df_pivot.dropna(
                        subset=[ano_inicial, ano_final], inplace=True)
                    df_pivot['variacao'] = df_pivot[ano_final] - \
                        df_pivot[ano_inicial]
                    df_resultado = df_pivot.groupby([segmentacao_id_evo, 'status_projeto'])[
                        'variacao'].mean().reset_index()
                    if not df_resultado.empty:
                        chart = alt.Chart(df_resultado).mark_bar().encode(x=alt.X('status_projeto:N', title="Possui Projeto?", axis=alt.Axis(labels=False, ticks=False)), y=alt.Y('variacao:Q', title=f'Variação Média da {indicador_nome_evo} (%)'), color=alt.Color('status_projeto:N', legend=alt.Legend(title="Possui Projeto?"), scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[
                            COR_LARANJA, '#888888'])), tooltip=[alt.Tooltip(segmentacao_id_evo, title=segmentacao_nome_evo), alt.Tooltip('status_projeto', title='Status'), alt.Tooltip('variacao', title='Redução Média', format='.2f')]).properties(width=100, height=350).facet(column=alt.Column(f'{segmentacao_id_evo}:N', title=segmentacao_nome_evo, sort=['Pequeno Porte', 'Médio Porte', 'Grande Porte', 'Metrópole']))
                        st.altair_chart(chart)

        st.divider()

        st.header(f"Contexto de Atuação do Instituto ({ano_selecionado})")
        st.markdown(
            f"Este gráfico ilustra o cenário que motiva o nosso trabalho. A comparação evidencia que os municípios onde o Instituto atua são o foco de nossa atenção justamente por partirem de indicadores mais desafiadores.")

        if df_filtrado.empty:
            st.warning(
                f"Nenhum dado disponível para os filtros selecionados no ano de {ano_selecionado}.")
        else:
            col_stat1, col_stat2 = st.columns(2)
            indicadores_static = {"Nota IDEB": "ideb_nota",
                                  "Taxa de Distorção": "taxa_distorcao_total_fun"}
            segmentacoes_static = {"População": "faixa_populacao",
                                   "PIB": "faixa_pib", "PIB per Capita": "faixa_pib_per_capita"}

            indicador_nome_static = col_stat1.selectbox(
                "Indicador para Análise Estática", options=list(indicadores_static.keys()))
            segmentacao_nome_static = col_stat2.selectbox(
                "Agrupar Análise Estática por", options=list(segmentacoes_static.keys()))

            indicador_id_static = indicadores_static[indicador_nome_static]
            segmentacao_id_static = segmentacoes_static[segmentacao_nome_static]

            df_impacto_static = df_filtrado.groupby([segmentacao_id_static, 'status_projeto']).agg(
                valor_medio=(indicador_id_static, 'mean')).reset_index()

            chart_static = alt.Chart(df_impacto_static).mark_bar().encode(
                x=alt.X(f'{segmentacao_id_static}:N', title=segmentacao_nome_static,
                        sort=None, axis=alt.Axis(labelAngle=0)),
                y=alt.Y('valor_medio:Q',
                        title=f"Média de {indicador_nome_static}"),
                color=alt.Color('status_projeto:N', title="Status", scale=alt.Scale(
                    domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, '#cccccc'])),
                xOffset='status_projeto:N',
                tooltip=[alt.Tooltip(segmentacao_id_static, title=segmentacao_nome_static), alt.Tooltip(
                    'status_projeto', title='Status'), alt.Tooltip('valor_medio', title='Valor Médio', format='.2f')]
            ).properties(height=400)

            st.altair_chart(chart_static, use_container_width=True)

    elif aba_selecionada == "Análise Histórica":
        st.header("Evolução Histórica do Município")
        st.markdown(
            "Acompanhe a tendência de um indicador para um município específico ao longo dos anos, destacando o período de atuação do Instituto.")

        municipios_disponiveis = sorted(
            df_filtrado['nome_municipio_formatado'].unique())

        if not municipios_disponiveis:
            st.warning(
                "Nenhum município disponível para os filtros selecionados.")
        else:
            indicadores_hist = {"Nota IDEB": "ideb_nota",
                                "Taxa de Distorção Idade-Série": "taxa_distorcao_total_fun"}

            col1, col2 = st.columns(2)
            municipio_selecionado = col1.selectbox(
                "Selecione o Município:", municipios_disponiveis)
            indicador_hist_nome = col2.selectbox(
                "Selecione o Indicador:", list(indicadores_hist.keys()))
            indicador_hist_id = indicadores_hist[indicador_hist_nome]

            if municipio_selecionado:
                # Filtra todos os dados históricos para o município selecionado
                df_historico_mun = df_completo[df_completo['nome_municipio_formatado']
                                               == municipio_selecionado].copy()
                df_historico_mun.dropna(
                    subset=[indicador_hist_id], inplace=True)

                if not df_historico_mun.empty:
                    # Encontra o primeiro ano de atuação
                    anos_com_projeto = df_historico_mun[df_historico_mun['tem_projeto'] == True]['ano']
                    ano_inicio_projeto = anos_com_projeto.min(
                    ) if not anos_com_projeto.empty else float('inf')

                    # Cria a coluna para a cor
                    df_historico_mun['status_atuacao'] = np.where(df_historico_mun['ano'] < ano_inicio_projeto,
                                                                  'Período sem Atuação', 'Período com Atuação')

                    # Cria o gráfico com a linha e os pontos
                    base = alt.Chart(df_historico_mun).encode(
                        x=alt.X('ano:O', title='Ano',
                                axis=alt.Axis(labelAngle=0)),
                        y=alt.Y(f'{indicador_hist_id}:Q',
                                title=indicador_hist_nome),
                        tooltip=[alt.Tooltip('ano', title='Ano'), alt.Tooltip(
                            indicador_hist_id, title='Valor', format='.2f'), 'status_atuacao']
                    )

                    linha = base.mark_line().encode(
                        color=alt.Color('status_atuacao:N',
                                        legend=alt.Legend(
                                            title="Status da Atuação"),
                                        scale=alt.Scale(domain=['Período com Atuação', 'Período sem Atuação'],
                                                        range=[COR_LARANJA, '#cccccc']))
                    )

                    pontos = base.mark_point(size=60, filled=True).encode(
                        color=alt.Color('status_atuacao:N', scale=alt.Scale(domain=['Período com Atuação', 'Período sem Atuação'],
                                                                            range=[COR_LARANJA, '#cccccc'])),
                        opacity=alt.value(1)
                    )

                    chart_hist = (linha + pontos).properties(
                        height=500, title=f"Evolução de {indicador_hist_nome} em {municipio_selecionado}"
                    )

                    st.altair_chart(chart_hist, use_container_width=True)
                else:
                    st.info(
                        "Não há dados históricos suficientes para este indicador no município selecionado.")

    elif aba_selecionada == "Análise de Correlação":
        st.header("Análise de Correlação: Fatores Socioeconômicos e Educacionais")
        if df_filtrado.empty:
            st.warning("Nenhum dado disponível para os filtros selecionados.")
        else:
            colunas_interesse = ['ideb_nota', 'pib_per_capita', 'populacao',
                                 'taxa_distorcao_total_fun', 'nr_projetos', 'nr_beneficiados']
            col1, col2 = st.columns(2)
            eixo_x = col1.selectbox("Eixo X", colunas_interesse, index=1)
            eixo_y = col2.selectbox("Eixo Y", colunas_interesse, index=0)

            df_corr = df_filtrado.dropna(subset=[eixo_x, eixo_y])
            scatter_chart = alt.Chart(df_corr).mark_circle(size=60, opacity=0.7).encode(x=alt.X(eixo_x, title=eixo_x.replace('_', ' ').title()), y=alt.Y(
                eixo_y, title=eixo_y.replace('_', ' ').title()), color=alt.value(COR_LARANJA), tooltip=['nome_municipio_formatado', eixo_x, eixo_y]).properties(height=500).interactive()
            st.altair_chart(scatter_chart, use_container_width=True)

    elif aba_selecionada == "Dados Detalhados":
        st.header("Dados Detalhados dos Municípios")
        busca = st.text_input("Buscar município...")
        df_tabela = df_filtrado
        if busca:
            df_tabela = df_tabela[df_tabela['nome_municipio_formatado'].str.contains(
                busca, case=False)]

        def destacar_projeto(linha):
            estilo = f'background-color: {COR_LARANJA}; color: white;' if linha.tem_projeto else ''
            return [estilo] * len(linha)

        colunas_para_exibir = ['nome_municipio_formatado', 'sg_uf', 'populacao', 'ideb_nota',
                               'pib_per_capita', 'nr_projetos', 'nr_beneficiados', 'taxa_distorcao_total_fun']

        st.dataframe(df_tabela[colunas_para_exibir + ['tem_projeto']].style.apply(destacar_projeto, axis=1),
                     column_config={'tem_projeto': None},
                     use_container_width=True)

        @st.cache_data
        def convert_df_to_csv(df):
            return df.to_csv(index=False).encode('utf-8')

        st.download_button(label="Exportar para CSV", data=convert_df_to_csv(
            df_tabela), file_name=f'dados_detalhados_{ano_selecionado}.csv', mime='text/csv')

    # RODAPÉ
    st.divider()
    desenvolvedores = "Leticia Braz Bonfim, Bianca Lavine da Silva Beserra, Kaio Vitor Martins"
    ano_rodape = 2025
    st.markdown(
        f'<div style="background-color: {COR_LARANJA}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-size: 14px;"><p style="margin:0;"><b>Desenvolvedores:</b> {desenvolvedores} | <b>Ano:</b> {ano_rodape}</p><p style="margin:0;">Projeto de Extensão da UFPB | Curso: Ciência de Dados para Negócios | Disciplina: Análise de Dados.</p></div>', unsafe_allow_html=True)


# --- PONTO DE ENTRADA PRINCIPAL DO SCRIPT ---
if __name__ == "__main__":
    df_principal = carregar_dados()
    if df_principal is not None:
        construir_dashboard(df_principal)

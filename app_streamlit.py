import streamlit as st
import pandas as pd
import altair as alt
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

# --- CONSTANTES DE ESTILO ---
COR_LARANJA = '#F68B1F'
COR_CINZA = '#cccccc'

# --- CSS CUSTOMIZADO PARA ESTILIZAR O BOTÃO DE DOWNLOAD ---
st.markdown(f"""
<style>
    div.stDownloadButton > button {{
        background-color: {COR_LARANJA};
        color: white;
        border: 2px solid {COR_LARANJA};
        border-radius: 5px;
    }}
    div.stDownloadButton > button:hover {{
        background-color: white;
        color: {COR_LARANJA};
        border: 2px solid {COR_LARANJA};
    }}
</style>
""", unsafe_allow_html=True)


# --- FUNÇÕES DE CARREGAMENTO DE DADOS ---
@st.cache_data
def carregar_dados():
    """Lê os dados processados e os enriquece com colunas para análise."""
    try:
        PROJETO_DIR = Path(__file__).parent
        PROCESSED_DATA_FILE = PROJETO_DIR / 'data' / 'processed' / 'data_final_consolidado.parquet'
        df = pd.read_parquet(PROCESSED_DATA_FILE)

        # --- Tratamentos e Criação de Novas Colunas ---
        df['nr_projetos'].fillna(0, inplace=True)
        df['nr_beneficiados'].fillna(0, inplace=True)
        df['tem_projeto'] = df['nr_projetos'] > 0
        df['status_projeto'] = np.where(df['tem_projeto'], 'Com Projetos', 'Sem Projetos')
        
        if 'id_municipio' in df.columns:
            df['id_municipio'] = df['id_municipio'].astype(str)

        if 'populacao' in df.columns:
            df['faixa_populacao'] = pd.qcut(df['populacao'], q=4, labels=['Pequeno Porte', 'Médio Porte', 'Grande Porte', 'Metrópole'], duplicates='drop')
        if 'pib_mil_reais' in df.columns:
            df['faixa_pib'] = pd.qcut(df['pib_mil_reais'], q=4, labels=['PIB Baixo', 'PIB Médio-Baixo', 'PIB Médio-Alto', 'PIB Alto'], duplicates='drop')
        if 'pib_per_capita' in df.columns:
            df['faixa_pib_per_capita'] = pd.qcut(df['pib_per_capita'], q=4, labels=['PIB per Capita Baixo', 'Médio-Baixo', 'Médio-Alto', 'Alto'], duplicates='drop')

        return df
    except FileNotFoundError:
        st.error(f"ERRO CRÍTICO: O arquivo de dados ('data_final_consolidado.parquet') não foi encontrado.")
        st.info("Certifique-se de que o arquivo está na pasta 'data/processed'.")
        return None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado ao carregar os dados: {e}")
        return None

@st.cache_data
def carregar_geojson(caminho_arquivo="data/raw/brasil_municipios.json"):
    """Carrega o arquivo GeoJSON com os contornos dos municípios."""
    try:
        caminho_completo = Path(__file__).parent / caminho_arquivo
        with open(caminho_completo, "r", encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"Arquivo GeoJSON do mapa não encontrado. A 'Análise Geográfica' será desativada.")
        return None

# --- PÁGINA DE AJUDA E GLOSSÁRIO (COM CONTEÚDO ATUALIZADO) ---
def pagina_ajuda():
    st.header("Ajuda & Glossário")
    st.markdown("Esta seção oferece explicações sobre os indicadores, visualizações e fontes de dados para garantir uma análise clara.")

    if st.button("⬅️ Voltar ao Dashboard"):
        st.session_state.pagina_ajuda_ativa = False
        st.rerun()

    st.divider()
    
    # --- SEÇÃO DE INDICADORES ATUALIZADA ---
    st.subheader("Glossário de Indicadores")

    with st.expander("**O que é IDEB?**"):
        st.markdown("""
        O **Índice de Desenvolvimento da Educação Básica (IDEB)** é o principal indicador de qualidade da educação no Brasil. Ele combina as notas dos alunos em exames nacionais com a taxa de aprovação escolar.
        - **Escala:** 0 a 10.
        - **Interpretação:** Quanto **maior** a nota, **melhor** a qualidade da educação.
        """)
    with st.expander("**O que é Taxa de Distorção Idade-Série?**"):
        st.markdown("""
        Mede a porcentagem de alunos com **dois ou mais anos de atraso escolar** em relação à idade esperada para a série. É um forte indicativo de problemas como repetência e evasão.
        - **Escala:** 0% a 100%.
        - **Interpretação:** Quanto **menor** a taxa, **melhor** o fluxo escolar e a progressão dos alunos.
        """)
    with st.expander("**O que é PIB per capita?**"):
        st.markdown("""
        É a riqueza total de um município (Produto Interno Bruto) dividida pelo número de habitantes. Serve como um indicador geral do contexto socioeconômico local.
        - **Interpretação:** Municípios com maior PIB per capita tendem a ter mais recursos, o que pode influenciar (mas não determinar) os investimentos em áreas como a educação.
        """)
    with st.expander("**O que são Faixas de População/PIB?**"):
        st.markdown("""
        Para permitir comparações mais justas, os municípios foram agrupados em "faixas" (quartis). Isso evita que um município muito pequeno seja comparado diretamente com uma grande metrópole.
        - **Exemplo:** 'Pequeno Porte', 'Médio Porte', 'Grande Porte', 'Metrópole'.
        - **Uso:** Na **Análise de Impacto**, usamos essas faixas para comparar a evolução de indicadores entre municípios de perfis semelhantes.
        """)
    
    st.divider()

    # --- NOVA SEÇÃO DE VISUALIZAÇÕES ---
    st.subheader("Entendendo as Visualizações")

    with st.expander("**Mapa de Atuação (Análise Geográfica)**"):
        st.markdown("""
        - **O que é?** É um mapa coroplético, onde as áreas (municípios) são coloridas de acordo com uma variável.
        - **Como interpretar neste dashboard?**
            - **Municípios Laranja:** Onde o Instituto Alpargatas **atua** com projetos.
            - **Municípios Cinza:** Onde o Instituto **não atua**, servindo como grupo de comparação.
            - Passe o mouse sobre um município para ver seus principais indicadores.
        """)
    with st.expander("**Gráfico de Barras Agrupadas (Análise de Impacto)**"):
        st.markdown("""
        - **O que é?** Um gráfico que usa barras para comparar valores médios entre diferentes grupos.
        - **Como interpretar neste dashboard?**
            - Ele compara a média de um indicador (como o IDEB) entre os municípios **Com Projetos (laranja)** e **Sem Projetos (cinza)**.
            - As comparações são feitas lado a lado para diferentes anos ou faixas (de população ou PIB), permitindo analisar se há uma evolução diferente entre os dois grupos.
        """)
    with st.expander("**Gráfico de Linha (Análise Histórica)**"):
        st.markdown("""
        - **O que é?** Um gráfico que mostra a evolução de um indicador ao longo do tempo.
        - **Como interpretar neste dashboard?**
            - Cada linha colorida representa um município que você selecionou.
            - O eixo horizontal (X) representa os anos, e o vertical (Y) o valor do indicador.
            - Permite visualizar se a tendência de um indicador está melhorando ou piorando para um ou mais municípios específicos.
        """)
    with st.expander("**Gráfico de Dispersão/Bolhas (Análise de Correlação)**"):
        st.markdown("""
        - **O que é?** Um gráfico que mostra a relação entre duas variáveis numéricas. No nosso caso, é também um gráfico de bolhas, pois o tamanho dos pontos tem um significado.
        - **Como interpretar neste dashboard?** Este gráfico mostra **três informações ao mesmo tempo**:
            - **Eixo X:** O valor do primeiro indicador que você selecionou.
            - **Eixo Y:** O valor do segundo indicador.
            - **Tamanho da Bolha:** A **população** do município. Bolhas maiores representam cidades mais populosas.
            - **Cor da Bolha:** Laranja para municípios **Com Projetos** e cinza para os **Sem Projetos**.
        - **Utilidade:** Ajuda a identificar se existe alguma tendência ou padrão entre os indicadores. Por exemplo: "Será que municípios com maior PIB per capita tendem a ter um IDEB maior?".
        """)

    st.divider()
    
    st.subheader("Fonte dos Dados")
    st.markdown("""
    - **INEP (Instituto Nacional de Estudos e Pesquisas Educacionais Anísio Teixeira):** IDEB (2005-2023) e Taxa de Distorção Idade-Série (TDI) (2019-2023).
    - **IBGE (Instituto Brasileiro de Geografia e Estatística):** Dados de municípios, População e PIB (2010-2021).
    - **Instituto Alpargatas:** Dados internos sobre número de projetos e beneficiados (2020-2025).

    *Observação: Os dados de População e PIB do IBGE, cuja última atualização oficial é de 2021, foram replicados para os anos de 2022 a 2025. Essa abordagem foi adotada para viabilizar a análise comparativa com os dados mais recentes do Instituto, mantendo um cenário socioeconômico consistente na ausência de novas publicações anuais do IBGE.*
    """)

# --- FUNÇÃO PRINCIPAL DO DASHBOARD ---
def construir_dashboard(df_completo, geojson_data):
    if 'pagina_ajuda_ativa' not in st.session_state:
        st.session_state.pagina_ajuda_ativa = False

    with st.sidebar:
        st.image("https://cdn.v2v.net/70fe53dd-da8c-48e8-8525-6e829825e319.png?v=63802404261", width=200)

        if st.button("Ajuda & Glossário", use_container_width=True):
            st.session_state.pagina_ajuda_ativa = True
            st.rerun()
        st.divider()

        st.title("Filtros")
        
    if st.session_state.pagina_ajuda_ativa:
        pagina_ajuda()
        return

    st.title("Dashboard Estratégico - Instituto Alpargatas")

    # --- Dentro da sua função construir_dashboard ---

    aba_selecionada = option_menu(
        menu_title=None,
        options=["Visão Geral", "Análise Geográfica", "Análise de Impacto", "Análise Histórica", "Análise de Correlação", "Dados Detalhados"],
        icons=['bar-chart-line', 'map', 'bullseye', 'graph-up', 'bezier2', 'table'],
        orientation="horizontal",
        styles={
                "container": {"padding": "0!important", "background-color": "#fafafa", "border-bottom": "2px solid #eee"},

                # Estado NÃO SELECIONADO (agora com um cinza escuro mais suave)
            "icon": {"color": "#FFFFFF", "font-size": "18px"},
            "nav-link": {
                "font-size": "14px",
                "text-align": "center",
                "margin": "0px",
                "--hover-color": "#eee",
                "color": "#555555"
            },

            # Estado SELECIONADO (continua como antes)
            "nav-link-selected": {
                "background-color": COR_LARANJA,
                "color": "white"
            },
            "icon--selected": {"color": "white"},
        }
    )

    # --- FILTROS GLOBAIS NA SIDEBAR ---
    with st.sidebar:
        # O filtro de ano é geral, mas a aba de Correlação terá sua própria lógica
        anos_disponiveis = sorted(df_completo['ano'].dropna().unique().astype(int), reverse=True)
        ano_selecionado = None
        if aba_selecionada not in ["Análise de Correlação"]:
             if aba_selecionada in ["Visão Geral", "Análise Geográfica", "Dados Detalhados"]:
                ano_selecionado = st.selectbox("Ano de Análise", anos_disponiveis)
             elif aba_selecionada == "Análise Histórica":
                ano_selecionado = st.selectbox("Ano de Destaque (linha vermelha)", anos_disponiveis)
             else: # Aba de Impacto
                ano_selecionado = anos_disponiveis[0] if anos_disponiveis else None

        # Filtro de estado é sempre global
        estados_disponiveis = sorted(df_completo['sg_uf'].dropna().unique())
        if 'estados_selecionados' not in st.session_state:
            st.session_state.estados_selecionados = estados_disponiveis

        selecao_manual = st.multiselect(
            "Estados (UF)",
            options=estados_disponiveis,
            default=st.session_state.estados_selecionados
        )

        if st.button("Selecionar Todos os Estados", use_container_width=True):
            st.session_state.estados_selecionados = estados_disponiveis
            st.rerun()

        if selecao_manual != st.session_state.estados_selecionados:
            st.session_state.estados_selecionados = selecao_manual
            st.rerun()

    # --- LÓGICA DE DADOS FILTRADOS ---
    # df_filtrado é usado pelas abas que dependem do filtro de ano global
    if ano_selecionado:
        df_filtrado = df_completo[(df_completo['ano'] == ano_selecionado) & (df_completo['sg_uf'].isin(st.session_state.estados_selecionados))]
    else:
        # Se não houver ano selecionado (como na aba de Correlação inicialmente), começa vazio
        df_filtrado = pd.DataFrame()


    # --- LÓGICA DE EXIBIÇÃO DAS ABAS ---
    if aba_selecionada == "Visão Geral":
        st.header(f"Resumo do Ano de {ano_selecionado}")
        if df_filtrado.empty:
            st.warning("Nenhum dado disponível para os filtros selecionados.")
        else:
            col1, col2, col3, col4 = st.columns(4)
            total_municipios = df_filtrado['id_municipio'].nunique()
            col1.metric("Municípios Analisados", total_municipios)
            status_counts = df_filtrado['status_projeto'].value_counts()
            com_projetos = status_counts.get('Com Projetos', 0)
            sem_projetos = status_counts.get('Sem Projetos', 0)
            col1.markdown(f"<small><b><span style='color:{COR_LARANJA};'>{com_projetos}</span></b> com projetos | <b>{sem_projetos}</b> sem projetos</small>", unsafe_allow_html=True)

            col2.metric("Projetos Ativos", int(df_filtrado['nr_projetos'].sum()))
            col3.metric("Estudantes Beneficiados", f"{int(df_filtrado['nr_beneficiados'].sum()):,}".replace(",", "."))
            
            ideb_medio = df_filtrado['ideb_nota'].mean()
            col4.metric("IDEB Médio (Público)", f"{ideb_medio:.2f}")
            ideb_min = df_filtrado['ideb_nota'].min()
            ideb_max = df_filtrado['ideb_nota'].max()
            col4.markdown(f"<small>Mínimo: <b><span style='color:{COR_LARANJA};'>{ideb_min:.2f}</span></b> | Máximo: <b><span style='color:{COR_LARANJA};'>{ideb_max:.2f}</span></b></small>", unsafe_allow_html=True)
            st.divider()

            st.subheader("Rankings Municipais")
            indicador_ranking = st.selectbox("Analisar por:", ["IDEB (maior para menor)", "Taxa de Distorção (menor para maior)"])
            
            if indicador_ranking == "IDEB (maior para menor)":
                df_rank = df_filtrado.sort_values(by='ideb_nota', ascending=False).dropna(subset=['ideb_nota'])
                cols_to_show = ['nome_municipio_formatado', 'ideb_nota', 'taxa_distorcao_total_fun']
                df_tail = df_rank[cols_to_show].tail(5).sort_values(by='ideb_nota', ascending=True)
            else:
                df_rank = df_filtrado.sort_values(by='taxa_distorcao_total_fun', ascending=True).dropna(subset=['taxa_distorcao_total_fun'])
                cols_to_show = ['nome_municipio_formatado', 'taxa_distorcao_total_fun', 'ideb_nota']
                df_tail = df_rank[cols_to_show].tail(5).sort_values(by='taxa_distorcao_total_fun', ascending=False)
            
            col_rank1, col_rank2 = st.columns(2)
            col_rank1.markdown('##### 🏆 Top 5 Melhores Resultados')
            col_rank1.dataframe(df_rank[cols_to_show].head(5).reset_index(drop=True), use_container_width=True)
            col_rank2.markdown('##### ⚠️ 5 Maiores Desafios')
            col_rank2.dataframe(df_tail.reset_index(drop=True), use_container_width=True)

    elif aba_selecionada == "Análise Geográfica":
        st.header(f"Mapa de Atuação e Análise Municipal em {ano_selecionado}")
        st.markdown("Passe o mouse sobre um município para ver detalhes.")
        if df_filtrado.empty or geojson_data is None:
            st.warning("Nenhum dado disponível para exibir no mapa com os filtros atuais.")
        else:
            fig = px.choropleth_mapbox(
                df_filtrado, geojson=geojson_data, locations='id_municipio', featureidkey="properties.id",
                color='status_projeto', color_discrete_map={'Com Projetos': COR_LARANJA, 'Sem Projetos': COR_CINZA},
                hover_name='nome_municipio_formatado',
                hover_data={'sg_uf': True, 'nr_projetos': True, 'nr_beneficiados': True, 'populacao': True, 'ideb_nota': ':.2f', 'pib_per_capita': ':.2f'},
                mapbox_style="carto-positron", zoom=4, center={"lat": -14.2350, "lon": -51.9253}, opacity=0.8
            )
            fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, legend_title_text='Status de Atuação')
            st.plotly_chart(fig, use_container_width=True)

    elif aba_selecionada == "Análise de Impacto":
        st.header("Análise da Evolução do Impacto (Comparativo)")
        st.markdown("Compare a evolução de um indicador entre dois anos, para municípios com e sem projetos, segmentado por uma característica.")

        col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
        indicadores_evolucao = {"Nota IDEB": "ideb_nota", "Taxa de Distorção": "taxa_distorcao_total_fun"}
        indicador_nome_evo = col_sel1.selectbox("Indicador para Análise de Evolução", options=list(indicadores_evolucao.keys()))
        indicador_id_evo = indicadores_evolucao[indicador_nome_evo]

        segmentacoes_evolucao = {"População": "faixa_populacao", "PIB": "faixa_pib", "PIB per Capita": "faixa_pib_per_capita"}
        segmentacao_nome_evo = col_sel2.selectbox("Agrupar Evolução por", options=list(segmentacoes_evolucao.keys()))
        segmentacao_id_evo = segmentacoes_evolucao[segmentacao_nome_evo]

        anos_validos = sorted(df_completo.dropna(subset=[indicador_id_evo])['ano'].unique().astype(int))
        
        if len(anos_validos) < 2:
            st.warning(f"Não há dados suficientes (pelo menos dois anos com dados) para a análise de evolução do indicador '{indicador_nome_evo}'.")
        else:
            ano_inicial = col_sel3.selectbox("Ano Inicial", options=anos_validos, index=0)
            ano_final = col_sel4.selectbox("Ano Final", options=anos_validos, index=len(anos_validos)-1)
            
            if ano_inicial is not None and ano_final is not None:
                if ano_inicial >= ano_final:
                    st.error("O Ano Inicial deve ser anterior ao Ano Final.")
                else:
                    df_periodo = df_completo[(df_completo['ano'].isin([ano_inicial, ano_final])) & (df_completo['sg_uf'].isin(st.session_state.estados_selecionados))].dropna(subset=[indicador_id_evo, segmentacao_id_evo])
                    
                    if df_periodo.empty:
                        st.info("Não há dados suficientes para a combinação de filtros selecionada.")
                    elif indicador_id_evo == 'ideb_nota':
                        df_agregado = df_periodo.groupby([segmentacao_id_evo, 'ano', 'status_projeto'])[indicador_id_evo].mean().reset_index()
                        chart = alt.Chart(df_agregado).mark_bar().encode(x=alt.X('ano:O', title="Ano", axis=alt.Axis(labelAngle=0)), y=alt.Y(f'{indicador_id_evo}:Q', title=f'Média de {indicador_nome_evo}'), color=alt.Color('status_projeto:N', title="Status", scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, COR_CINZA])), xOffset='status_projeto:N', tooltip=[alt.Tooltip(segmentacao_id_evo, title=segmentacao_nome_evo), alt.Tooltip('ano', title='Ano'), alt.Tooltip('status_projeto', title='Status'), alt.Tooltip(indicador_id_evo, title='Valor Médio', format='.2f')]).properties(width=180).facet(column=alt.Column(f'{segmentacao_id_evo}:N', title=segmentacao_nome_evo, sort=None)).configure_view(stroke=None)
                        st.altair_chart(chart, use_container_width=True)
                    elif indicador_id_evo == 'taxa_distorcao_total_fun':
                        df_pivot = df_periodo.pivot_table(index=['id_municipio', segmentacao_id_evo, 'status_projeto'], columns='ano', values=indicador_id_evo).reset_index()
                        df_pivot.dropna(subset=[ano_inicial, ano_final], inplace=True)
                        if df_pivot.empty:
                            st.info("Não há dados suficientes para calcular a variação (municípios precisam ter dados nos dois anos).")
                        else:
                            df_pivot['variacao'] = df_pivot[ano_final] - df_pivot[ano_inicial]
                            df_resultado = df_pivot.groupby([segmentacao_id_evo, 'status_projeto'])['variacao'].mean().reset_index()
                            chart = alt.Chart(df_resultado).mark_bar().encode(x=alt.X('status_projeto:N', title="Status", axis=alt.Axis(labels=False, ticks=False)), y=alt.Y('variacao:Q', title=f'Variação Média de {indicador_nome_evo}'), color=alt.Color('status_projeto:N', legend=alt.Legend(title="Status"), scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, COR_CINZA])), tooltip=[alt.Tooltip(segmentacao_id_evo, title=segmentacao_nome_evo), alt.Tooltip('status_projeto', title='Status'), alt.Tooltip('variacao', title='Variação Média', format='.2f')]).properties(width=100).facet(column=alt.Column(f'{segmentacao_id_evo}:N', title=segmentacao_nome_evo, sort=None))
                            st.altair_chart(chart)

        st.divider()

        st.header(f"Contexto de Atuação do Instituto ({ano_selecionado})")
        st.markdown(f"Este gráfico ilustra o cenário que motiva o nosso trabalho...")
        if df_filtrado.empty:
            st.warning(f"Nenhum dado disponível para os filtros selecionados no ano de {ano_selecionado}.")
        else:
            col_stat1, col_stat2 = st.columns(2)
            indicadores_static = {"Nota IDEB": "ideb_nota", "Taxa de Distorção": "taxa_distorcao_total_fun"}
            segmentacoes_static = {"População": "faixa_populacao", "PIB": "faixa_pib", "PIB per Capita": "faixa_pib_per_capita"}
            indicador_nome_static = col_stat1.selectbox("Indicador para Análise Estática", options=list(indicadores_static.keys()))
            segmentacao_nome_static = col_stat2.selectbox("Agrupar Análise Estática por", options=list(segmentacoes_static.keys()))
            indicador_id_static = indicadores_static[indicador_nome_static]
            segmentacao_id_static = segmentacoes_static[segmentacao_nome_static]
            df_impacto_static = df_filtrado.groupby([segmentacao_id_static, 'status_projeto']).agg(valor_medio=(indicador_id_static, 'mean')).reset_index()
            chart_static = alt.Chart(df_impacto_static).mark_bar().encode(x=alt.X(f'{segmentacao_id_static}:N', title=segmentacao_nome_static, sort=None, axis=alt.Axis(labelAngle=0)), y=alt.Y('valor_medio:Q', title=f"Média de {indicador_nome_static}"), color=alt.Color('status_projeto:N', title="Status", scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, COR_CINZA])), xOffset='status_projeto:N', tooltip=[alt.Tooltip(segmentacao_id_static, title=segmentacao_nome_static), alt.Tooltip('status_projeto', title='Status'), alt.Tooltip('valor_medio', title='Valor Médio', format='.2f')]).properties(height=400)
            st.altair_chart(chart_static, use_container_width=True)

    elif aba_selecionada == "Análise Histórica":
        st.header("Evolução Histórica Comparativa")
        with st.sidebar:
            indicadores_hist = {"Nota IDEB": "ideb_nota", "Taxa de Distorção Idade-Série": "taxa_distorcao_total_fun"}
            indicador_hist_nome = st.selectbox("Selecione o Indicador:", list(indicadores_hist.keys()))
            indicador_hist_id = indicadores_hist[indicador_hist_nome]
            
            municipios_disponiveis = sorted(df_completo[df_completo['sg_uf'].isin(st.session_state.estados_selecionados)]['nome_municipio_formatado'].unique())
            municipios_selecionados = st.multiselect("Municípios para Comparar:", municipios_disponiveis, default=[municipios_disponiveis[0]] if municipios_disponiveis else [])

        if not municipios_selecionados:
            st.warning("Selecione ao menos um município na barra lateral.")
        else:
            df_hist = df_completo[df_completo['nome_municipio_formatado'].isin(municipios_selecionados)].dropna(subset=[indicador_hist_id])
            if not df_hist.empty:
                base = alt.Chart(df_hist).encode(x=alt.X('ano:O', title='Ano'), y=alt.Y(f'{indicador_hist_id}:Q', title=indicador_hist_nome, scale=alt.Scale(zero=False)), color=alt.Color('nome_municipio_formatado:N', title="Município"), tooltip=['nome_municipio_formatado', 'ano', alt.Tooltip(indicador_hist_id, title='Valor', format='.2f')])
                linha = base.mark_line()
                pontos = base.mark_point(size=80, filled=True)
                if ano_selecionado:
                    regra = alt.Chart(pd.DataFrame({'x': [ano_selecionado]})).mark_rule(color='red', strokeDash=[4,4]).encode(x='x:O')
                    st.altair_chart((linha + pontos + regra).properties(height=450).interactive(), use_container_width=True)
                else:
                    st.altair_chart((linha + pontos).properties(height=450).interactive(), use_container_width=True)
            else:
                st.info("Não há dados históricos para este indicador no(s) município(s) selecionado(s).")
    
    elif aba_selecionada == "Análise de Correlação":
        ano_selecionado_corr = None
        
        with st.sidebar:
            st.header("Filtros de Correlação")
            colunas_corr = {'Nota IDEB': 'ideb_nota', 'PIB per Capita': 'pib_per_capita', 'População': 'populacao', 'Taxa de Distorção': 'taxa_distorcao_total_fun', 'Nº de Projetos': 'nr_projetos'}
            eixo_x_nome = st.selectbox("Eixo X:", list(colunas_corr.keys()), index=1)
            eixo_y_nome = st.selectbox("Eixo Y:", list(colunas_corr.keys()), index=0)
            eixo_x, eixo_y = colunas_corr[eixo_x_nome], colunas_corr[eixo_y_nome]

            # Filtra dinamicamente os anos que possuem dados para AMBOS os eixos selecionados
            anos_validos_corr = sorted(
                df_completo.dropna(subset=[eixo_x, eixo_y])['ano'].unique().astype(int),
                reverse=True
            )

            if not anos_validos_corr:
                st.warning(f"Não há dados anuais disponíveis para a combinação de '{eixo_x_nome}' e '{eixo_y_nome}'.")
            else:
                ano_selecionado_corr = st.selectbox("Ano de Análise para Correlação", anos_validos_corr, key="ano_corr_selectbox")

        # Lógica de exibição no painel principal
        if ano_selecionado_corr:
            st.header(f"Fatores Socioeconômicos e Educacionais em {ano_selecionado_corr}")
            
            df_corr_filtrado = df_completo[
                (df_completo['ano'] == ano_selecionado_corr) &
                (df_completo['sg_uf'].isin(st.session_state.estados_selecionados))
            ].dropna(subset=[eixo_x, eixo_y])

            if not df_corr_filtrado.empty:
                chart = alt.Chart(df_corr_filtrado).mark_circle(opacity=0.8).encode(
                    x=alt.X(eixo_x, title=eixo_x_nome, scale=alt.Scale(zero=False)), 
                    y=alt.Y(eixo_y, title=eixo_y_nome, scale=alt.Scale(zero=False)), 
                    color=alt.Color('status_projeto:N', title="Status", scale=alt.Scale(domain=['Com Projetos', 'Sem Projetos'], range=[COR_LARANJA, COR_CINZA])), 
                    size=alt.Size('populacao', title='População', legend=None, scale=alt.Scale(type="log", range=[20, 500])), 
                    tooltip=['nome_municipio_formatado', eixo_x, eixo_y, 'populacao'],
                    order=alt.Order('tem_projeto:N', sort='ascending'),
                    stroke=alt.condition(
                        "datum.status_projeto == 'Com Projetos'",
                        alt.value('white'),
                        alt.value(None)
                    ),
                    strokeWidth=alt.value(1)
                ).properties(height=500).interactive()
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("Não há dados para os filtros de estado selecionados neste ano. Tente selecionar outros estados.")
        else:
            st.header("Análise de Correlação")
            st.info(f"Selecione os eixos na barra lateral para começar. Se nenhum ano aparecer para seleção, significa que não há dados para a combinação de '{eixo_x_nome}' e '{eixo_y_nome}'.")

    elif aba_selecionada == "Dados Detalhados":
        st.header(f"Dados Detalhados dos Municípios ({ano_selecionado})")
        busca = st.text_input("Buscar município...")
        df_tabela = df_filtrado
        if busca:
            df_tabela = df_tabela[df_tabela['nome_municipio_formatado'].str.contains(busca, case=False, na=False)]

        def destacar_projeto(linha):
            if linha.tem_projeto:
                return [f'background-color: {COR_LARANJA}; color: white;'] * len(linha)
            else:
                return [''] * len(linha)

        colunas_para_exibir = ['nome_municipio_formatado', 'sg_uf', 'populacao', 'ideb_nota', 'pib_per_capita', 'nr_projetos', 'nr_beneficiados', 'taxa_distorcao_total_fun']
        
        if not df_tabela.empty:
            df_display = df_tabela[colunas_para_exibir + ['tem_projeto']]
            st.dataframe(
                df_display.style.apply(destacar_projeto, axis=1),
                column_config={'tem_projeto': None},
                use_container_width=True
            )

            @st.cache_data
            def convert_df_to_csv(df):
                return df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="Exportar para CSV", 
                data=convert_df_to_csv(df_tabela[colunas_para_exibir]), 
                file_name=f'dados_detalhados_{ano_selecionado}.csv', 
                mime='text/csv'
            )
        else:
            st.warning("Nenhum dado detalhado para exibir com os filtros atuais.")


    # --- RODAPÉ ---
    st.divider()
    desenvolvedores = "Leticia Braz Bonfim, Bianca Lavine da Silva Beserra, Kaio Vitor Martins da Silva"
    ano_rodape = 2025
    st.markdown(f'<div style="background-color: {COR_LARANJA}; padding: 10px; border-radius: 5px; text-align: center; color: white; font-size: 14px;"><p style="margin:0;"><b>Desenvolvedores:</b> {desenvolvedores} | <b>Ano:</b> {ano_rodape}</p><p style="margin:0;">Projeto de Extensão da UFPB | Curso: Ciência de Dados para Negócios | Disciplina: Análise de Dados.</p></div>', unsafe_allow_html=True)


# --- PONTO DE ENTRADA DO SCRIPT ---
if __name__ == "__main__":
    df_principal = carregar_dados()
    geojson_principal = carregar_geojson()
    if df_principal is not None:
        construir_dashboard(df_principal, geojson_principal)
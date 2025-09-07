# Importar as bibliotecas
import streamlit as st
import pandas as pd
import altair as alt

# Importar o DataFrame final processado
# Acessamos o DataFrame final que já foi criado e salvo pelo script data_processing.py
from data_processing import data_final

# Criar as funções de carregamento de dados


@st.cache_data
def carregar_dados():
    # Use o DataFrame 'data_final' diretamente, que já foi processado
    # Você pode querer adicionar um tratamento final aqui se necessário, mas por enquanto,
    # vamos usar o que já está pronto.
    dados = data_final
    return dados


# Carregar e limpar os dados
dados = carregar_dados()

# Exibir o título e a descrição do seu app
st.title("Visualização de Dados do IDEB 2005-2023")
st.markdown(
    "Em relação ao tema Combatendo a Evasão Escolar em parceria com o **Instituto Alpargatas**")

# Crie a lista de municípios únicos que existem no seu conjunto de dados
# Agora, a coluna de nome do município é 'nome_municipio_formatado' no DataFrame final
lista_municipios = dados['nome_municipio_formatado'].unique()

# Crie o menu de seleção para o usuário escolher o município
municipio_selecionado = st.selectbox(
    'Selecione o Município para Visualizar o IDEB',
    lista_municipios
)

# Filtre os dados com base na escolha do usuário
dados_municipio = dados[dados['nome_municipio_formatado']
                        == municipio_selecionado]

# Selecione as colunas do IDEB de 2005 a 2023
colunas_ideb = [f'ideb_{ano}' for ano in range(2005, 2024, 2)]
dados_ideb = dados_municipio[colunas_ideb]

# Use pd.melt para transformar as colunas de ano em uma única coluna 'Ano' e os valores em 'IDEB'
dados_para_plotar = pd.melt(dados_ideb, var_name='Ano', value_name='IDEB')

# Converta a coluna 'Ano' para string para plotagem
dados_para_plotar['Ano'] = dados_para_plotar['Ano'].str.replace('ideb_', '')
dados_para_plotar['IDEB'] = pd.to_numeric(
    dados_para_plotar['IDEB'], errors='coerce')
dados_para_plotar = dados_para_plotar.fillna(0)

# Crie o gráfico de linha com o Altair
chart = alt.Chart(dados_para_plotar).mark_line(point=True).encode(
    x=alt.X('Ano:N', title='Ano'),
    y=alt.Y('IDEB:Q', title='IDEB'),
    tooltip=[
        alt.Tooltip('Ano:N', title='Ano'),
        alt.Tooltip('IDEB:Q', title='IDEB')
    ]
).properties(
    title=f'Evolução do IDEB para {municipio_selecionado}'
)

# Exiba o gráfico no seu aplicativo
st.altair_chart(chart, use_container_width=True)

# Opcional: Mostre uma tabela dos dados filtrados para conferência
st.subheader(f"Dados do IDEB para {municipio_selecionado}")
st.dataframe(dados_ideb)

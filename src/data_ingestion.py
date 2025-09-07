'''
Funções responsáveis pela leitura dos dados brutos (raw):
- DTB_relatorio_br_municipios.xls
- IDEB_anos_iniciais_2023.xlsx
- projetos_IA_2020-2025.xlsx
'''

import pandas as pd
from pathlib import Path
from paths import diretorio_DTB, diretorio_IDEB, diretorio_PROJ_IA


def ler_dtb(diretorio_DTB: Path):
    '''
    Função para leitura dos dados da Divisão Geográfica do Brasil (DTB) - Municípios
    '''
    df_dtb_bruto = pd.read_excel(diretorio_DTB, skiprows=6,
                                 usecols=['UF', 'Nome_UF', 'Nome Região Geográfica Imediata',
                                          'Código Município Completo', 'Nome_Município'])

    # print(' DATA FRAME BRUTO: Divisão Geográfica do Brasil (DTB) '.center(150, '='))
    # print('INSPEÇÃO PRIMEIRAS LINHAS\n','---'*10, df_dtb_bruto.head(), '\n')
    # print('INSPEÇÃO ULTIMAS LINHAS \n','---'*10, df_dtb_bruto.tail(), '\n')
    # print('INFO \n', '---'*10)
    # df_dtb_bruto.info()

    return df_dtb_bruto


def ler_ideb(diretorio_IDEB: Path):
    '''
    Função para leitura dos dados do Índice de Desenvolvimento da Educação Básica (Ideb)
    '''
    lista_ideb = [f'VL_OBSERVADO_{x}' for x in range(2005, 2025, 2)]

    df_ideb_bruto = pd.read_excel(diretorio_IDEB, skiprows=9,
                                  usecols=['CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE'] + lista_ideb,
                                  na_values=['-', '--'])

    # print(' DATA FRAME BRUTO: Índice de Desenvolvimento da Educação Básica (Ideb) '.center(150, '='))
    # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---' * 10, '\n', df_ideb_bruto.head(), '\n')
    # print('INFO \n', '---'*10)
    # df_ideb_bruto.info()

    return df_ideb_bruto


def ler_proj_IA(diretorio_PROJ_IA: Path):
    '''
    Função para leitura dos dados do arquivo Projetos IA
    '''
    df_proj_IA_bruto = pd.read_excel(diretorio_PROJ_IA, sheet_name='2024', skiprows=5,
                                     usecols=['CIDADES', 'UF', 'Nº \nProjetos.7',
                                              'Nº \nInstituições.1', 'Nº \nBeneficiados.4'])

    # print(' DATA FRAME BRUTO: PROJETOS IA '.center(150, '='))
    # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---' * 10, '\n', df_proj_IA_bruto.head(), '\n')
    # print('INFO \n', '---'*10)
    # df_proj_IA_bruto.info()

    return df_proj_IA_bruto


df_dtb_bruto = ler_dtb(diretorio_DTB)
df_ideb_bruto = ler_ideb(diretorio_IDEB)
df_proj_IA_bruto = ler_proj_IA(diretorio_PROJ_IA)


'''

# --- ETAPA 1: UNIR OS DATAFRAMES (APÓS A LEITURA DOS ARQUIVOS) ---

# Limpeza e padronização dos dados antes da união

# 1. Padronizar a coluna 'nome_municipio' em ambos os DataFrames
df_IA_data['nome_municipio'] = df_IA_data['nome_municipio'].str.strip().str.upper()
df_dtb_data['nome_municipio'] = df_dtb_data['nome_municipio'].str.strip().str.upper()

# 2. Padronizar a coluna 'id_municipio' para que ambos os DataFrames tenham o mesmo tipo
# O IDEB tem IDs como float, então vamos convertê-los para inteiro
df_ideb_data['id_municipio'] = df_ideb_data['id_municipio'].fillna(
    0).astype(int)

# Agora, vamos tentar a união novamente com os dados limpos
df_projetos_municipios = pd.merge(
    df_IA_data, df_dtb_data, on='nome_municipio', how='left')

# Verificamos se a união deu certo antes de prosseguir
print("Tamanho do DataFrame de projetos e municípios após a primeira união:",
      df_projetos_municipios.shape)

# Unir o resultado com df_ideb_data usando o 'id_municipio' como chave
df_combinado = pd.merge(df_projetos_municipios,
                        df_ideb_data, on='id_municipio', how='inner')

# Verificamos se a segunda união deu certo
print("Tamanho do DataFrame final após a segunda união:", df_combinado.shape)

# --- ETAPA 2: ANÁLISE E PREPARAÇÃO PARA O GRÁFICO ---

# Crie uma nova coluna para identificar se o município tem projetos ou não
df_combinado['tem_projeto'] = df_combinado['nr_projetos'] > 0

# Agrupe os dados por rede e se tem projeto para calcular a média do IDEB de 2023
media_ideb_por_grupo = df_combinado.groupby(['tem_projeto', 'rede'])[
    'ideb_2023'].mean().reset_index()

# Renomeie a coluna booleana para algo mais legível para o gráfico
media_ideb_por_grupo['tem_projeto'] = media_ideb_por_grupo['tem_projeto'].replace(
    {True: 'Com Projeto', False: 'Sem Projeto'})

# --- ETAPA 3: GERAR O NOVO GRÁFICO ---


fig, ax = plt.subplots(figsize=(12, 7))

redes = media_ideb_por_grupo['rede'].unique()
x = np.arange(len(redes))

width = 0.35
# Barras para municípios SEM projetos
sem_projeto_data = media_ideb_por_grupo[media_ideb_por_grupo['tem_projeto']
                                        == 'Sem Projeto']['ideb_2023']
ax.bar(x - width/2, sem_projeto_data, width, label='Sem Projeto')

# Barras para municípios COM projetos
com_projeto_data = media_ideb_por_grupo[media_ideb_por_grupo['tem_projeto']
                                        == 'Com Projeto']['ideb_2023']
ax.bar(x + width/2, com_projeto_data, width, label='Com Projeto')

ax.set_ylabel('Média do IDEB')
ax.set_title('Média do IDEB (2023) por Rede de Ensino e Presença de Projetos')
ax.set_xticks(x)
ax.set_xticklabels(redes)
ax.legend()

plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.show()

df_combinado.to_csv('conjunto_de_dados_final.csv', index=False)
'''

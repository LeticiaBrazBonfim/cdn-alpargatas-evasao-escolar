'''
Funções responsáveis pela leitura dos dados brutos (raw):
- DTB_relatorio_br_municipios.xls
- IDEB_anos_iniciais_2023.xlsx
- projetos_IA_2020-2025.xlsx
- PIB_municípios_2010-2021.xlsx
'''

import pandas as pd
from pathlib import Path
from paths import diretorio_DTB, diretorio_IDEB, diretorio_PROJ_IA, diretorio_PIB


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
    abas_anos = ['2020', '2021']
    dfs = []

    for aba in abas_anos:
        df_temp = pd.read_excel(diretorio_PROJ_IA, sheet_name=aba, header=5,
                                usecols=['CIDADES', 'ESTADO', 'Nº de Projetos',
                                        'Nº de Instituições', 'Nº de Beneficiados'])

        # Adiciona a coluna 'ano' em cada DataFrame
        df_temp['ano'] = int(aba)
        dfs.append(df_temp)

    # Junta todas as abas de anos
    df_proj_IA_bruto = pd.concat(dfs, ignore_index=True)
    
    # print(' DATA FRAME BRUTO: Projetos IA '.center(150, '='))
    # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, df_proj_IA_bruto.head(), '\n')
    # print('INSPEÇÃO ULTIMAS LINHAS \n', '---'*10, df_proj_IA_bruto.tail(), '\n')
    # print('INFO \n', '---'*10)
    # df_proj_IA_bruto.info()

    return df_proj_IA_bruto



def ler_pib(diretorio_PIB: Path):
    '''
    Função para leitura dos dados do Produto Interno Bruto (PIB) - Municípios
    '''
    df_pib_bruto = pd.read_excel(diretorio_PIB,
                                 usecols=['Ano', 'Nome da Grande Região', 'Código do Município',
                                          'Nome do Município', 'Sigla da Unidade da Federação',
                                          'Produto Interno Bruto, \na preços correntes\n(R$ 1.000)',
                                          'Produto Interno Bruto per capita, \na preços correntes\n(R$ 1,00)'])

    # print(' DATA FRAME BRUTO: Produto Interno Bruto (PIB) '.center(150, '='))
    # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, df_pib_bruto.head(), '\n')
    # print('INSPEÇÃO ULTIMAS LINHAS \n', '---'*10, df_pib_bruto.tail(), '\n')
    # print('INFO \n', '---'*10)
    # df_pib_bruto.info()

    return df_pib_bruto


df_dtb_bruto = ler_dtb(diretorio_DTB)
df_ideb_bruto = ler_ideb(diretorio_IDEB)
df_proj_IA_bruto = ler_proj_IA(diretorio_PROJ_IA)
df_pib_bruto = ler_pib(diretorio_PIB)

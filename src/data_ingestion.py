'''
Funções responsáveis pela leitura dos dados brutos (raw):
- DTB_relatorio_br_municipios.xls
- IDEB_anos_iniciais_2023.xlsx
- projetos_IA_2020-2025.xlsx
- PIB_municípios_2010-2021.xlsx

Este arquivo funciona como uma biblioteca de ferramentas para o main.py.
'''
import paths as pth
from pathlib import Path
import pandas as pd
import sys

'''
Funções responsáveis pela leitura dos dados brutos (raw):
- DTB_relatorio_br_municipios.xls
- IDEB_anos_iniciais_2023.xlsx
- projetos_IA_2020-2025.xlsx
- PIB_municípios_2010-2021.xlsx

Este arquivo funciona como uma biblioteca de ferramentas para o main.py.
'''


def exibir_erro_e_sair(nome_arquivo: str, diretorio: Path):
    '''
    Exibe uma mensagem de erro padronizada e encerra o script.
    '''
    print('/'*80 + '\n')
    print(f'ERRO CRÍTICO: Arquivo "{nome_arquivo}" não foi encontrado.')
    print(f'O script esperava encontrá-lo em: "{diretorio}"')
    print('/'*80 + '\n')

    print('''Possíveis Causas:
        1. O arquivo pode ter sido renomeado, movido ou excluído.
        2. O nome do arquivo definido no script "paths.py" está diferente do nome real do arquivo.
        3. A estrutura de pastas esperada (ex: "data/raw/DTB/") não existe ou foi alterada.''')
    print(f'''\nSugestões de Resolução:
        - Verifique se o arquivo "{nome_arquivo}" está presente na pasta correta.
        - Confira se não há erros de digitação no nome do arquivo ou das pastas no script "paths.py".
        - Certifique-se de que o script está sendo executado a partir da pasta raiz do projeto.''')

    print('\n> Por esse motivo o script será encerrado neste instante.')
    sys.exit(1)


def ler_dtb(diretorio_DTB: Path):
    '''
    Função para leitura dos dados da Divisão Geográfica do Brasil (DTB) - Municípios
    '''
    try:
        df_dtb_bruto = pd.read_excel(diretorio_DTB, skiprows=6,
                                    usecols=['UF', 'Nome_UF', 'Nome Região Geográfica Imediata',
                                            'Código Município Completo', 'Nome_Município'])
        print(f"INFO: Arquivo '{pth.file_dtb}' lido com sucesso.")

        # print(' DATA FRAME BRUTO: Divisão Geográfica do Brasil (DTB) '.center(150, '='))
        # print('INSPEÇÃO PRIMEIRAS LINHAS\n','---'*10, df_dtb_bruto.head(), '\n')
        # print('INSPEÇÃO ULTIMAS LINHAS \n','---'*10, df_dtb_bruto.tail(), '\n')
        # print('INFO \n', '---'*10)
        # df_dtb_bruto.info()

        return df_dtb_bruto
    except FileNotFoundError:
        exibir_erro_e_sair(pth.file_dtb, diretorio_DTB)


def ler_ideb(diretorio_IDEB: Path):
    '''
    Função para leitura dos dados do Índice de Desenvolvimento da Educação Básica (Ideb)
    '''
    try:
        lista_ideb = [f'VL_OBSERVADO_{x}' for x in range(2005, 2025, 2)]

        df_ideb_bruto = pd.read_excel(diretorio_IDEB, skiprows=9,
                                    usecols=[
                                        'CO_MUNICIPIO', 'NO_MUNICIPIO', 'REDE'] + lista_ideb,
                                    na_values=['-', '--'])
        print(f'INFO: Arquivo "{pth.file_ideb}" lido com sucesso.')

        # print(' DATA FRAME BRUTO: Índice de Desenvolvimento da Educação Básica (Ideb) '.center(150, '='))
        # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---' * 10, '\n', df_ideb_bruto.head(), '\n')
        # print('INFO \n', '---'*10)
        # df_ideb_bruto.info()

        return df_ideb_bruto
    except FileNotFoundError:
        exibir_erro_e_sair(pth.file_ideb, diretorio_IDEB)


def ler_proj_IA(diretorio_PROJ_IA: Path):
    '''
    Função para leitura dos dados do arquivo Projetos IA
    '''
    try:
        abas_anos = ['2020', '2021', '2022', '2023', '2024', '2025']
        df_final = []

        for aba in abas_anos:
            df_anos = pd.read_excel(diretorio_PROJ_IA, sheet_name=aba,
                                    usecols=['CIDADES', 'ESTADO', 'Nº de Projetos',
                                            'Nº de Instituições', 'Nº de Beneficiados'],
                                    na_values=['-', '--'])

            # Adiciona a coluna 'ano' em cada DataFrame
            df_anos['ano'] = int(aba)
            df_final.append(df_anos)

        # Junta todas as abas de anos
        df_proj_IA_bruto = pd.concat(df_final, ignore_index=True)

        print(f'INFO: Arquivo "{pth.file_proj_IA}" lido com sucesso.')

        # print(' DATA FRAME BRUTO: Projetos IA '.center(150, '='))
        # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, df_proj_IA_bruto.head(), '\n')
        # print('INSPEÇÃO ULTIMAS LINHAS \n', '---'*10, df_proj_IA_bruto.tail(), '\n')
        # print('INFO \n', '---'*10)
        # df_proj_IA_bruto.info()

        return df_proj_IA_bruto
    except FileNotFoundError:
        exibir_erro_e_sair(pth.file_proj_IA, diretorio_PROJ_IA)


def ler_pib(diretorio_PIB: Path):
    '''
    Função para leitura dos dados do Produto Interno Bruto (PIB) - Municípios
    '''
    try:
        df_pib_bruto = pd.read_excel(diretorio_PIB,
                                    usecols=['Ano', 'Nome da Grande Região', 'Código do Município',
                                            'Nome do Município', 'Sigla da Unidade da Federação',
                                            'Produto Interno Bruto, \na preços correntes\n(R$ 1.000)',
                                            'Produto Interno Bruto per capita, \na preços correntes\n(R$ 1,00)'],
                                    na_values=['-', '--'])
        print(f'INFO: Arquivo "{pth.file_pib}" lido com sucesso.')

        # print(' DATA FRAME BRUTO: Produto Interno Bruto (PIB) '.center(150, '='))
        # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, df_pib_bruto.head(), '\n')
        # print('INSPEÇÃO ULTIMAS LINHAS \n', '---'*10, df_pib_bruto.tail(), '\n')
        # print('INFO \n', '---'*10)
        # df_pib_bruto.info()

        return df_pib_bruto
    except FileNotFoundError:
        exibir_erro_e_sair(pth.file_pib, diretorio_PIB)
        

def ler_taxa_distorcao(diretorio_TAXA_DISTORCAO: Path):
    '''
    Função para leitura dos dados de Taxa de Distorção Idade-Série - Municípios
    '''
    try:
        df_taxa_distorcao = pd.read_excel(diretorio_TAXA_DISTORCAO, skiprows=8,
                                        usecols=['NU_ANO_CENSO', 'CO_MUNICIPIO', 'NO_MUNICIPIO', 'NO_DEPENDENCIA',
                                                'FUN_CAT_0', 'FUN_AI_CAT_0', 'FUN_AF_CAT_0'],
                                        na_values=['-', '--'])

        print(
            f'INFO: Arquivo "{diretorio_TAXA_DISTORCAO.name}" lido com sucesso.')

        # print(' DATA FRAME BRUTO: Taxa de Distorção Idade-Série por Município - 2023 '.center(150, '='))
        # print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---' *
        #         10, df_taxa_distorcao.head(), '\n')
        # print('INSPEÇÃO ULTIMAS LINHAS \n', '---' *
        #         10, df_taxa_distorcao.tail(), '\n')
        # print('INFO \n', '---'*10)
        # df_taxa_distorcao.info()

        return df_taxa_distorcao
    except FileNotFoundError:
        exibir_erro_e_sair(diretorio_TAXA_DISTORCAO.name,
                           diretorio_TAXA_DISTORCAO)

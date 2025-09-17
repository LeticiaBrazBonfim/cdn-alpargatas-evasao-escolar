'''
Funções responsáveis pelo tratamento dos dados brutos (raw):
- Padronização
- Tratamento e limpeza
- Agregação
- União
- Geração de dados processados

Este arquivo funciona como uma biblioteca de ferramentas para o main.py.
'''
import pandas as pd
from paths import PROCESSED_DATA_DIR


def formatar_nome(df, coluna):
    return (df[coluna].str.upper()
            .str.replace('MIXING CENTER', '')
            .str.replace(r'[-.!?"`()*]', '', regex=True)
            .str.strip()
            .str.replace('  ', ' ')
            .str.normalize('NFKD')  # Normaliza caracteres acentuados
            .str.encode('ascii', errors='ignore')  # Remove acentos
            .str.decode('utf-8'))  # Decodifica novamente


def tratar_dtb(df):
    df = (df.rename(columns={
        'UF': 'id_uf',
        'Nome_UF': 'nome_uf',
        'Nome Região Geográfica Imediata': 'nome_rgi',
        'Código Município Completo': 'id_municipio',
        'Nome_Município': 'nome_municipio'
    })
        .drop_duplicates(subset=['id_municipio'])
    )

    df['nome_municipio_formatado'] = formatar_nome(df, 'nome_municipio')
    df = df.drop(columns=['nome_municipio'])

    print(' DATA FRAME TRATADO: Divisão Geográfica do Brasil (DTB) '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df


def tratar_ideb(df):
    rename_map = {
        'CO_MUNICIPIO': 'id_municipio',
        'NO_MUNICIPIO': 'nome_municipio',
        'REDE': 'rede'
    }
    # Adiciona os nomes das colunas de notas do IDEB ao dicionário
    for year in range(2005, 2025, 2):
        rename_map[f'VL_OBSERVADO_{year}'] = f'ideb_{year}'

    df = df.rename(columns=rename_map)

    df_longo = pd.melt(df,
                       id_vars=['id_municipio', 'nome_municipio', 'rede'],
                       value_vars=[f'ideb_{x}' for x in range(2005, 2025, 2)],
                       var_name='ano_str',
                       value_name='ideb_nota')

    df_longo['ano'] = df_longo['ano_str'].str.replace('ideb_', '').astype(int)
    df = df_longo.query('rede == "Pública"').copy()
    df = df_longo.drop(columns=['ano_str'])

    df = df.dropna(subset=['id_municipio'])
    df['id_municipio'] = df['id_municipio'].astype(int)
    df['nome_municipio_formatado'] = formatar_nome(df, 'nome_municipio')
    df = df.drop(columns=['nome_municipio'])

    print(' DATA FRAME TRATADO: Índice de Desenvolvimento da Educação Básica (Ideb) '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df


def tratar_proj_IA(df):
    df = df.rename(columns={
        'CIDADES': 'nome_municipio',
        'ESTADO': 'sg_uf',
        'Nº de Projetos': 'nr_projetos',
        'Nº de Instituições': 'nr_instituicoes',
        'Nº de Beneficiados': 'nr_beneficiados'})

    # Adiciona a coluna 'ano' para o merge
    df['ano'] = df['ano'].astype(int)

    # Limpeza adicional: remove linhas que não são de municípios válidos
    df = df.dropna(subset=['sg_uf']).copy()

    df['nome_municipio_formatado'] = formatar_nome(df, 'nome_municipio')
    df = df.drop(columns=['nome_municipio'])

    df = (df.groupby(['nome_municipio_formatado', 'sg_uf', 'ano'])
            .agg({
                'nr_projetos': 'sum',
                'nr_instituicoes': 'sum',
                'nr_beneficiados': 'sum'
            })
          .reset_index()
          )

    mapa_uf = {
        'PB': 'Paraíba',
        'PE': 'Pernambuco',
        'MG': 'Minas Gerais',
        'SP': 'São Paulo',
        'RJ': 'Rio de Janeiro'
    }

    df['nome_uf'] = df['sg_uf'].map(mapa_uf)

    print(' DATA FRAME TRATADO: PROJETOS IA '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df


def tratar_pib(df):
    df = df.rename(columns={
        'Ano': 'ano',
        'Nome da Grande Região': 'regiao',
        'Código do Município': 'id_municipio',
        'Nome do Município': 'nome_municipio',
        'Sigla da Unidade da Federação': 'sg_uf',
        'Produto Interno Bruto, \na preços correntes\n(R$ 1.000)': 'pib_mil_reais',
        'Produto Interno Bruto per capita, \na preços correntes\n(R$ 1,00)': 'pib_per_capita'
    })

    # df = df.query('ano in [2020, 2021]')

    df['nome_municipio_formatado'] = formatar_nome(df, 'nome_municipio')
    df = df.drop(columns=['nome_municipio'])

    # Converter para numérico
    for col in ['pib_mil_reais', 'pib_per_capita']:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calcular população estimada
    df['populacao'] = (df['pib_mil_reais'] * 1000) / df['pib_per_capita']

    # Limpar valores nulos
    df = df.dropna(subset=['id_municipio', 'pib_mil_reais', 'pib_per_capita'])
    
    # Lógica para preencher os anos faltantes (2022-2025) com os dados do último ano (2021)
    ultimo_ano = df['ano'].max()
    anos_futuros = pd.DataFrame({'ano': [2022, 2023, 2024, 2025]})
    df_ultimo_ano = df.loc[df['ano'] == ultimo_ano]
    df_replicado = df_ultimo_ano.drop(
        columns='ano').merge(anos_futuros, how='cross')
    df = pd.concat([df, df_replicado], ignore_index=True)

    print(
        f'-> PIB tratado e replicado de {ultimo_ano} até {df["ano"].max()}.')

    print(' DATA FRAME TRATADO: Produto Interno Bruto (PIB) '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df

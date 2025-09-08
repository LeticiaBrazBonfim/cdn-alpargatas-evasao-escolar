'''
Funções responsáveis pelo tratamento dos dados brutos (raw):
- Padronização
- Tratamento e limpeza
- Agregação
- União
- Geração de dados processados
'''

from paths import PROCESSED_DATA_DIR
from data_ingestion import df_dtb_bruto, df_ideb_bruto, df_proj_IA_bruto, df_pib_bruto
import pandas as pd


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
    novos_nomes = ['id_municipio', 'nome_municipio', 'rede'] + \
        [f'ideb_{x}' for x in range(2005, 2025, 2)]
    df = df.rename(columns=dict(zip(df.columns, novos_nomes)))

    df_longo = pd.melt(df,
                       id_vars=['id_municipio', 'nome_municipio', 'rede'],
                       value_vars=[f'ideb_{x}' for x in range(2005, 2025, 2)],
                       var_name='ano_str',
                       value_name='ideb_nota')

    df_longo['ano'] = df_longo['ano_str'].str.replace('ideb_', '').astype(int)
    df = df_longo.drop(columns=['ano_str'])

    # Adiciona .copy() para evitar o SettingWithCopyWarning
    # df = df.query("ano in [2020, 2021] and rede == 'Pública'").copy()

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

    print(' DATA FRAME TRATADO: Produto Interno Bruto (PIB) '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df

df_dtb_tratado = tratar_dtb(df_dtb_bruto)
df_ideb_tratado = tratar_ideb(df_ideb_bruto)
df_proj_IA_tratado = tratar_proj_IA(df_proj_IA_bruto)
df_pib_tratado = tratar_pib(df_pib_bruto)

# Salva os dfs tratados em data/processed
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

df_dtb_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'dtb_consolidado.parquet', index=False)
df_ideb_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'ideb_consolidado.parquet', index=False)
df_proj_IA_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'proj_IA_consolidado.parquet', index=False)
df_pib_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'pib_consolidado.parquet', index=False)


# Mescla os dfs
# PIB é a base principal
data_final = df_pib_tratado.merge(
    # Adiciona os dados do IDEB. Junção: 'id_municipio' e 'ano'
    df_ideb_tratado.drop(columns=['nome_municipio_formatado']),
    how='left',
    on=['id_municipio', 'ano']
).merge(
    # Adiciona os dados geográficos da DTB. Como a DTB não tem ano, unimos apenas por 'id_municipio'. 
    # As informações serão replicadas para cada ano.
    df_dtb_tratado.drop(columns=['nome_municipio_formatado']),
    how='left',
    on='id_municipio'
)

# Adicionamos os dados dos projetos_IA.
# Junção: 'nome_municipio_formatado' e 'nome_uf' da DTB, junto com o ano.
data_final = data_final.merge(
    df_proj_IA_tratado.drop(columns=['sg_uf']),
    how='left',
    on=['nome_municipio_formatado', 'nome_uf', 'ano']
)

print('\n-> DataFrames consolidados salvos com sucesso na pasta "processed"!\n')

print(' DATA FRAME FINAL (após união DTB, IDEB, PROJ IA e PIB) '.center(150, '='))
print(data_final.dropna(subset=['nr_projetos']).head())
print('\nVerificação das colunas do DataFrame final:')
print(data_final.info())

# Salva o DataFrame final, que contém todos os 3 dfs unidos
data_final.to_parquet(PROCESSED_DATA_DIR /
                      'data_final_consolidado.parquet', index=False)

print('\n--- DataFrame final salvo com sucesso! ---')

'''
Funções responsáveis pelo tratamento dos dados brutos (raw):
- Padronização
- Tratamento e limpeza
- Agregação
- União
- Geração de dados processados
'''

from paths import PROCESSED_DATA_DIR
from data_ingestion import df_dtb_bruto, df_ideb_bruto, df_proj_IA_bruto
import pandas as pd


def formatar_nome(df, coluna):
    return (df[coluna].str.upper()
                    .str.replace('MIXING CENTER', '')
                    .str.replace(r'[-.!?"`()]', '', regex=True)
                    .str.strip() 
                    .str.replace(' ', '_'))

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
        'UF': 'sg_uf',
        'Nº \nProjetos.7': 'nr_projetos',
        'Nº \nInstituições.1': 'nr_instituicoes',
        'Nº \nBeneficiados.4': 'nr_beneficiados'})

    df['nome_municipio_formatado'] = formatar_nome(df, 'nome_municipio')
    df = df.drop(columns=['nome_municipio'])

    df = (df.groupby('nome_municipio_formatado')
            .agg({
                'sg_uf': 'first',
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
        'SP': 'São Paulo'
    }
    df['nome_uf'] = df['sg_uf'].map(mapa_uf)

    print(' DATA FRAME TRATADO: PROJETOS IA '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', df.head(), '\n')
    print('INFO \n', '---'*10)
    df.info()

    return df

df_dtb_tratado = tratar_dtb(df_dtb_bruto)
df_ideb_tratado = tratar_ideb(df_ideb_bruto)
df_proj_IA_tratado = tratar_proj_IA(df_proj_IA_bruto)

# Salva os dfs tratados em data/processed
PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

df_dtb_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'dtb_consolidado.parquet', index=False)
df_ideb_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'ideb_consolidado.parquet', index=False)
df_proj_IA_tratado.to_parquet(
    PROCESSED_DATA_DIR / 'proj_IA_consolidado.parquet', index=False)

print('\n-> DataFrames consolidados salvos com sucesso na pasta "processed"!\n')

# Mescla dos dfs
data_m = df_proj_IA_tratado.merge(
    df_dtb_tratado,
    how='left',
    on=['nome_municipio_formatado', 'nome_uf'],
    suffixes=['_IA', '_DTB'],
    indicator='tipo_merge'
)

n_encontrados_dtb = data_m.query('tipo_merge=="left_only"')
print(' MUNICÍPIOS DE PROJETOS IA NÃO ENCONTRADOS NA BASE DTB '.center(150, '='))
print(n_encontrados_dtb.head())

data_final = data_m.merge(
    df_ideb_tratado,
    how='left',
    on=['nome_municipio_formatado', 'id_municipio']
)

print(' DATA FRAME FINAL (após união DTB, IDEB e PROJ IA) '.center(150, '='))
print(data_final.head())


# Salva o DataFrame final, que contém todos os 3 dfs unidos
data_final.to_parquet(PROCESSED_DATA_DIR /
                    'data_final_consolidado.parquet', index=False)

print('\n--- DataFrame final salvo com sucesso! ---')



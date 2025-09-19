import pandas as pd
import paths as pth  # Importar os caminhos de entrada
from paths import PROCESSED_DATA_DIR  # Importar o caminho de saída
from data_processing import tratar_dtb, tratar_ideb, tratar_proj_IA, tratar_pib, tratar_taxa_distorcao
from data_ingestion import ler_dtb, ler_ideb, ler_proj_IA, ler_pib, ler_taxa_distorcao

# Importar as ferramentas necessárias
def executar_pipeline():
    '''
    Orquestra a execução completa do pipeline de dados,
    desde a ingestão até o salvamento do arquivo final.
    '''
    print(':.: Iniciando Pipeline de Dados :.:')

    # ETAPA DE INGESTÃO: Usando as ferramentas de 'data_ingestion.py'
    print('1/4: Lendo arquivos brutos...')
    df_dtb_bruto = ler_dtb(pth.diretorio_DTB)
    df_ideb_bruto = ler_ideb(pth.diretorio_IDEB)
    df_proj_IA_bruto = ler_proj_IA(pth.diretorio_PROJ_IA)
    df_pib_bruto = ler_pib(pth.diretorio_PIB)
    df_taxa_distorcao_2021_bruto = ler_taxa_distorcao(pth.diretorio_TAXA_DISTORCAO_2021)
    df_taxa_distorcao_2023_bruto = ler_taxa_distorcao(pth.diretorio_TAXA_DISTORCAO_2023)
    print('* Arquivos lidos com sucesso!')

    # ETAPA DE PROCESSAMENTO: Usando as ferramentas de 'data_processing.py'
    print('\n2/4: Processando e limpando dados...')
    df_dtb_tratado = tratar_dtb(df_dtb_bruto)
    df_dtb_tratado.to_parquet(
        PROCESSED_DATA_DIR / 'dtb_consolidado.parquet', index=False)

    df_ideb_tratado = tratar_ideb(df_ideb_bruto)
    df_ideb_tratado.to_parquet(
        PROCESSED_DATA_DIR / 'ideb_consolidado.parquet', index=False)

    df_proj_IA_tratado = tratar_proj_IA(df_proj_IA_bruto)
    df_proj_IA_tratado.to_parquet(
        PROCESSED_DATA_DIR / 'proj_IA_consolidado.parquet', index=False)

    df_pib_tratado = tratar_pib(df_pib_bruto)
    df_pib_tratado.to_parquet(
        PROCESSED_DATA_DIR / 'pib_consolidado.parquet', index=False)
    
    df_taxa_distorcao_2021_tratado = tratar_taxa_distorcao(df_taxa_distorcao_2021_bruto)
    df_taxa_distorcao_2023_tratado = tratar_taxa_distorcao(df_taxa_distorcao_2023_bruto)
    
    # --- CONSOLIDAÇÃO DOS DADOS DE DISTORÇÃO ---
    # Junta 2021 com o de 2023
    df_taxa_distorcao_final = pd.concat(
        [df_taxa_distorcao_2021_tratado, df_taxa_distorcao_2023_tratado],
        ignore_index=True
    )

    print('\n* Dados de Taxa de Distorção de 2021 e 2023 foram unificados.')

    df_taxa_distorcao_final.to_parquet(
        PROCESSED_DATA_DIR / 'taxa_distorcao_consolidado.parquet', index=False
    )

    # ETAPA DE UNIÃO DE DATAFRAMES
    print('\n3/4: Unindo DataFrames...')
    data_final = df_pib_tratado.merge(
        df_ideb_tratado.drop(columns=['nome_municipio_formatado']),
        how='left',
        on=['id_municipio', 'ano']
    ).merge(
        df_dtb_tratado.drop(columns=['nome_municipio_formatado']),
        how='left',
        on='id_municipio'
    ).merge(
        df_proj_IA_tratado.drop(columns=['sg_uf']),
        how='left',
        on=['nome_municipio_formatado', 'nome_uf', 'ano']
    ).merge(
        df_taxa_distorcao_final.drop(columns=['nome_municipio_formatado']),
        how='left',
        on=['id_municipio', 'ano']
    )

    print(' DATA FINAL CONSOLIDADO '.center(150, '='))
    print('INSPEÇÃO PRIMEIRAS LINHAS\n', '---'*10, '\n', data_final.head(), '\n')
    print('INFO \n', '---'*10)
    data_final.info()
    
    print('\n4/4: Salvando o DataFrame final...')
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    data_final.to_parquet(PROCESSED_DATA_DIR /
                            'data_final_consolidado.parquet', index=False)
    print('* DataFrame final salvo com sucesso!')

    print("\n=== Pipeline concluído ===")


if __name__ == "__main__":
    executar_pipeline()

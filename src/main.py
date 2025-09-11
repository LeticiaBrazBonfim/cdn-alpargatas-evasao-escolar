# Importar as ferramentas necessárias
from data_ingestion import ler_dtb, ler_ideb, ler_proj_IA, ler_pib
from data_processing import tratar_dtb, tratar_ideb, tratar_proj_IA, tratar_pib, formatar_nome
from paths import PROCESSED_DATA_DIR  # Importar o caminho de saída
import paths as pth  # Importar os caminhos de entrada


def executar_pipeline():
   '''
   Orquestra a execução completa do pipeline de dados,
   desde a ingestão até o salvamento do arquivo final.
   '''
   print(':.: Iniciando pipeline de dados :.:')

   # ETAPA DE INGESTÃO: Usando as ferramentas de 'data_ingestion.py'
   print('1/4: Lendo arquivos brutos...')
   df_dtb_bruto = ler_dtb(pth.diretorio_DTB)
   df_ideb_bruto = ler_ideb(pth.diretorio_IDEB)
   df_proj_IA_bruto = ler_proj_IA(pth.diretorio_PROJ_IA)
   df_pib_bruto = ler_pib(pth.diretorio_PIB)
   print('* Arquivos lidos com sucesso!')

   # ETAPA DE PROCESSAMENTO: Usando as ferramentas de 'data_processing.py'
   print('\n2/4: Processando e limpando dados...')
   df_dtb_tratado = tratar_dtb(df_dtb_bruto)
   df_ideb_tratado = tratar_ideb(df_ideb_bruto)
   df_proj_IA_tratado = tratar_proj_IA(df_proj_IA_bruto)
   df_pib_tratado = tratar_pib(df_pib_bruto)
   print('* Dados processados com sucesso!')

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
   )

   print('\n4/4: Salvando o DataFrame final...')
   PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
   data_final.to_parquet(PROCESSED_DATA_DIR /
                        'data_final_consolidado.parquet', index=False)
   print('* DataFrame final salvo com sucesso!')
   
   print("\n=== Pipeline concluído ===")


if __name__ == "__main__":
   executar_pipeline()

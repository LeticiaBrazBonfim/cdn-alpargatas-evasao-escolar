import pandas as pd
from pathlib import Path


def verificar_arquivo_final():
    '''
    Lê o arquivo de dados processado e exibe um resumo para diagnóstico.
    '''
    print("--- INICIANDO VERIFICAÇÃO DO ARQUIVO FINAL ---")

    try:
        # Constrói o caminho para o arquivo de dados
        # Este script está em 'src/', então subimos um nível para o diretório do projeto
        caminho_arquivo = Path(__file__).resolve(
        ).parent.parent / 'data' / 'processed' / 'data_final_consolidado.parquet'

        print(f"Tentando ler o arquivo em: {caminho_arquivo}")

        # Lê o arquivo parquet
        df = pd.read_parquet(caminho_arquivo)

        print("\n✅ SUCESSO: Arquivo lido com sucesso!")

        # Exibe informações essenciais do DataFrame
        print("\n--- Informações Gerais ---")
        print(f"Formato do DataFrame (linhas, colunas): {df.shape}")
        df.info()

        # Ponto mais importante: verificar os anos presentes
        print("\n--- Verificação de Anos ---")
        anos_presentes = sorted(df['ano'].unique())
        print(f"Anos únicos no arquivo: {anos_presentes}")

        # Amostra dos dados para anos críticos
        print("\n--- Amostra de Dados para 2023 ---")
        df_2023 = df[df['ano'] == 2023]
        if df_2023.empty:
            print("NENHUMA LINHA ENCONTRADA PARA O ANO DE 2023.")
        else:
            # Mostra colunas chave para verificar se os merges funcionaram
            colunas_chave = [
                'id_municipio', 'ano', 'nome_municipio_formatado', 'nome_uf',
                'pib_per_capita', 'ideb_nota', 'nr_projetos'
            ]
            # Filtra colunas que existem no dataframe para evitar erros
            colunas_existentes = [
                col for col in colunas_chave if col in df.columns]
            print(df_2023[colunas_existentes].head())

    except FileNotFoundError:
        print("\n❌ ERRO CRÍTICO: O arquivo 'data_final_consolidado.parquet' não foi encontrado!")
        print("Isso indica que o script main.py não está conseguindo salvar o arquivo no local esperado.")
    except Exception as e:
        print(f"\n❌ Ocorreu um erro inesperado ao ler o arquivo: {e}")


if __name__ == "__main__":
    verificar_arquivo_final()

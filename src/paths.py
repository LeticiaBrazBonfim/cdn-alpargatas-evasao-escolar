from pathlib import Path

# Encontra o diretório de dados brutos(raw)
PROJETO_DIR = Path(__file__).parent.parent

# Define os diretórios de dados brutos e processados de forma portátil
RAW_DATA_DIR = PROJETO_DIR / 'data' / 'raw'
PROCESSED_DATA_DIR = PROJETO_DIR / 'data' / 'processed'

# Nomes e caminhos completos de cada arquivo, incluindo a subpasta
file_dtb = 'DTB_relatorio_br_municipios_2024.xls'
file_ideb = 'IDEB_anos_iniciais_2023.xlsx'
file_proj_IA = 'projetos_IA_2020-2025.xlsx'
file_pib = 'PIB_municípios_2010-2021.xlsx'
file_taxa_distorcao_2021 = 'TDI_MUNICIPIOS_2021.xlsx'
file_taxa_distorcao_2023 = 'TDI_MUNICIPIOS_2023.xlsx'

# Cria o caminho completo para cada arquivo
diretorio_DTB = RAW_DATA_DIR / 'DTB' / file_dtb
diretorio_IDEB = RAW_DATA_DIR / 'IDEB' / file_ideb
diretorio_PROJ_IA = RAW_DATA_DIR / 'proj_IA' / file_proj_IA
diretorio_PIB = RAW_DATA_DIR / 'PIB' / file_pib
diretorio_TAXA_DISTORCAO_2021 = RAW_DATA_DIR / 'IDEB' / file_taxa_distorcao_2021
diretorio_TAXA_DISTORCAO_2023 = RAW_DATA_DIR / 'IDEB' / file_taxa_distorcao_2023



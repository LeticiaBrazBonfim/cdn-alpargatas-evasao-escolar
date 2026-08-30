"""
Pré-processamento: converte Excel brutos (data/raw/) em Parquet (data/processed/).

Uso: python scripts/data_processing.py

Fluxo completo: Excel → Parquet → dbt (DuckDB) → Metabase
"""

import logging
import time
from pathlib import Path

import polars as pl
from openpyxl import load_workbook

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Diretórios
RAIZ = Path(__file__).resolve().parent.parent.parent
RAW_DIR = RAIZ / "data" / "raw"
PROCESSED_DIR = RAIZ / "data" / "processed"

# Fontes Excel
EXCEL_DTB = RAW_DIR / "DTB_relatorio_br_municipios_2024.xls"
EXCEL_PIB = RAW_DIR / "PIB_municípios_2010-2023.xlsx"
EXCEL_PROJ = RAW_DIR / "projetos_IA_2020-2025.xlsx"
EXCEL_IDEB = RAW_DIR / "IDEB_anos_iniciais_2023.xlsx"

# Mapeamento IBGE: código numérico → sigla da UF (fixo, não muda)
UF_SIGLAS = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA",
    "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
    "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE",
    "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT",
    "52": "GO", "53": "DF",
}


def _dedup_colunas(nomes):
    """Gera nomes de coluna únicos com sufixo .N para duplicatas.

    Replica o comportamento do Pandas ao concatenar DataFrames com
    colunas homônimas: a primeira ocorrência fica sem sufixo, as
    demais recebem .1, .2, etc. Colunas vazias viram 'Unnamed: N'.
    """
    visto = {}
    resultado = []
    contador_unnamed = 0
    for n in nomes:
        texto = "" if n is None else str(n).strip()
        if texto == "" or texto == "None":
            resultado.append(f"Unnamed: {contador_unnamed}")
            contador_unnamed += 1
        else:
            if texto in visto:
                visto[texto] += 1
                resultado.append(f"{texto}.{visto[texto]}")
            else:
                visto[texto] = 0
                resultado.append(texto)
    return resultado


def _ler_excel_sem_cabecalho(caminho, linha_cabecalho):
    """Lê Excel preservando os nomes originais das colunas.

    O engine calamine (default do Polars) dropa linhas vazias
    automaticamente, deslocando os índices. Esta função lê sem
    cabeçalho, seleciona a linha correta e renomeia manualmente.
    """
    df_raw = pl.read_excel(caminho, has_header=False, infer_schema_length=0)
    assert df_raw.height > linha_cabecalho, f"Arquivo muito curto: {caminho.name}"

    cabecalho = [str(v) for v in df_raw.row(linha_cabecalho)]
    cabecalho = _dedup_colunas(cabecalho)

    df = df_raw.slice(linha_cabecalho + 1).rename(
        dict(zip(df_raw.columns, cabecalho))
    )
    assert df.height > 0, f"Arquivo vazio: {caminho.name}"
    return df.cast(pl.Utf8)


def salvar(df, nome):
    """Salva DataFrame como Parquet em data/processed/."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.write_parquet(PROCESSED_DIR / f"{nome}.parquet")
    logging.info(f"  ✓ {nome}: {df.height:,} linhas × {df.width} colunas")


def main():
    inicio = time.perf_counter()
    logging.info("Convertendo Excel → Parquet...\n")

    # 1. DTB — Diretório Territorial Brasileiro
    #    Calamine dropa 2 linhas vazias → cabeçalho na linha 4 (0-indexed)
    #    Injeta sigla_uf a partir do código numérico (o DTB do IBGE não tem essa coluna)
    df_dtb = _ler_excel_sem_cabecalho(EXCEL_DTB, linha_cabecalho=4)
    df_dtb = df_dtb.with_columns(
        pl.col("UF").replace_strict(UF_SIGLAS, default=None).alias("sigla_uf")
    )
    salvar(df_dtb, "dtb_municipios")

    # 2. PIB — Produto Interno Bruto municipal (2010-2021)
    #    Sem metadado; cabeçalho na primeira linha
    df = pl.read_excel(EXCEL_PIB)
    df.columns = _dedup_colunas(df.columns)
    salvar(df.cast(pl.Utf8), "pib_municipios")

    # 3. Projetos IA — cada aba = um ano (2020..2025)
    #    Abas têm colunas diferentes; lê sem cabeçalho para preservar nomes
    #    originais e aplica dedup com sufixo .N (compatível com Pandas)
    wb = load_workbook(EXCEL_PROJ, read_only=True)
    abas_numericas = [a for a in wb.sheetnames if a.isdigit()]
    wb.close()

    dfs = []
    for aba in abas_numericas:
        df_raw = pl.read_excel(
            EXCEL_PROJ, sheet_name=aba, has_header=False, infer_schema_length=0
        )
        cabecalho = _dedup_colunas([str(v) for v in df_raw.row(0)])
        df = df_raw.slice(1).rename(dict(zip(df_raw.columns, cabecalho)))
        df = df.cast(pl.Utf8).with_columns(pl.lit(int(aba)).alias("ano"))
        dfs.append(df)

    salvar(pl.concat(dfs, how="diagonal"), "projetos_ia")

    # 4. IDEB — Índice de Desenvolvimento da Educação Básica
    #    Cabeçalho real com nomes de coluna (SG_UF, CO_MUNICIPIO, etc.) na linha 7
    salvar(_ler_excel_sem_cabecalho(
        EXCEL_IDEB, linha_cabecalho=7), "ideb_municipios")

    # 5. TDI — Taxa de Distorção Idade-Série (1 arquivo por ano)
    #    Calamine dropa 2 linhas vazias → cabeçalho na linha 6 (0-indexed)
    arquivos = sorted(RAW_DIR.glob("TDI_MUNICIPIOS_*.xlsx"))
    assert arquivos, f"Nenhum arquivo TDI encontrado em {RAW_DIR}"

    dfs = []
    for arq in arquivos:
        df_raw = pl.read_excel(arq, has_header=False, infer_schema_length=0)
        cabecalho = _dedup_colunas([str(v) for v in df_raw.row(6)])
        df = df_raw.slice(7).rename(dict(zip(df_raw.columns, cabecalho)))
        dfs.append(df.cast(pl.Utf8))

    salvar(pl.concat(dfs), "taxa_distorcao")

    logging.info(f"\n✅ Concluído em {time.perf_counter() - inicio:.1f}s")


if __name__ == "__main__":
    main()

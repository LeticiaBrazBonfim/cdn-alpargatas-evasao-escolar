import argparse
import csv
import os
from io import StringIO
from pathlib import Path

import duckdb
import psycopg2
from psycopg2 import sql
import yaml


DEFAULT_PROFILE = "alpargatas-impacto-educacional"


def load_yaml(path):
    with path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def project_profile_name(project_dir):
    project = load_yaml(project_dir / "dbt_project.yml")
    return project.get("profile", DEFAULT_PROFILE)


def profile_path(profiles_dir):
    if profiles_dir:
        return Path(profiles_dir) / "profiles.yml"
    if os.getenv("DBT_PROFILES_DIR"):
        return Path(os.environ["DBT_PROFILES_DIR"]) / "profiles.yml"
    return Path.home() / ".dbt" / "profiles.yml"


def target_config(profile_name, profiles_file, target_name):
    profiles = load_yaml(profiles_file)
    profile = profiles[profile_name]
    selected_target = target_name or os.getenv("DBT_TARGET") or profile.get("target", "dev")
    config = profile["outputs"][selected_target].copy()
    config["_target_name"] = selected_target
    return config


def postgres_connection(config):
    return psycopg2.connect(
        dbname=config.get("dbname") or config.get("database"),
        user=config.get("user"),
        password=config.get("password"),
        host=config.get("host"),
        port=config.get("port", 5432),
        sslmode=config.get("sslmode", "require"),
        connect_timeout=30,
    )


def normalize(value):
    if value is None:
        return r"\N"
    return str(value)


def copy_batch(pg_cursor, connection, schema, table_name, columns, rows):
    buffer = StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerows([normalize(value) for value in row] for row in rows)
    buffer.seek(0)

    copy_sql = sql.SQL(
        "copy {}.{} ({}) from stdin with (format csv, null '\\N')"
    ).format(
        sql.Identifier(schema),
        sql.Identifier(table_name),
        sql.SQL(", ").join(sql.Identifier(column) for column in columns),
    )
    pg_cursor.copy_expert(copy_sql.as_string(connection), buffer)


def table_exists(pg_cursor, schema, table_name):
    pg_cursor.execute(
        """
        select exists (
            select 1
            from information_schema.tables
            where table_schema = %s
              and table_name = %s
        )
        """,
        (schema, table_name),
    )
    return pg_cursor.fetchone()[0]


def prepare_table(pg_cursor, schema, table_name, columns, if_exists):
    exists = table_exists(pg_cursor, schema, table_name)
    if exists and if_exists == "skip":
        return False
    if exists and if_exists == "fail":
        raise RuntimeError(
            f"{schema}.{table_name} ja existe. Use --if-exists skip para manter "
            "ou --if-exists replace para recarregar."
        )
    if exists and if_exists == "replace":
        pg_cursor.execute(
            sql.SQL("drop table {}.{}").format(
                sql.Identifier(schema),
                sql.Identifier(table_name),
            )
        )

    pg_cursor.execute(
        sql.SQL("create table {}.{} ({})").format(
            sql.Identifier(schema),
            sql.Identifier(table_name),
            sql.SQL(", ").join(
                sql.SQL("{} text").format(sql.Identifier(column)) for column in columns
            ),
        )
    )
    return True


def load_parquet(duck_connection, pg_connection, schema, path, batch_size, if_exists):
    table_name = path.stem
    parquet_path = path.as_posix()
    duck_cursor = duck_connection.execute("select * from read_parquet(?)", [parquet_path])
    columns = [column[0] for column in duck_cursor.description]

    with pg_connection.cursor() as pg_cursor:
        pg_cursor.execute(sql.SQL("create schema if not exists {}").format(sql.Identifier(schema)))
        should_load = prepare_table(pg_cursor, schema, table_name, columns, if_exists)
        if not should_load:
            print(f"{schema}.{table_name}: tabela existente mantida")
            return

        total_rows = 0
        while True:
            rows = duck_cursor.fetchmany(batch_size)
            if not rows:
                break
            copy_batch(pg_cursor, pg_connection, schema, table_name, columns, rows)
            total_rows += len(rows)

    pg_connection.commit()
    print(f"{schema}.{table_name}: {total_rows} linhas carregadas")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Carrega os Parquets de data/raw como tabelas raw no Postgres/Neon."
    )
    parser.add_argument("--target", help="Target do profiles.yml. Padrao: target do perfil.")
    parser.add_argument("--schema", default="raw", help="Schema de destino. Padrao: raw.")
    parser.add_argument("--profiles-dir", help="Diretorio que contem profiles.yml.")
    parser.add_argument(
        "--if-exists",
        choices=("fail", "skip", "replace"),
        default="fail",
        help="Comportamento quando a tabela raw ja existe. Padrao: fail.",
    )
    parser.add_argument("--batch-size", type=int, default=10000)
    return parser.parse_args()


def main():
    args = parse_args()
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    repo_dir = project_dir.parent
    data_dir = repo_dir / "data" / "raw"

    profiles_file = profile_path(args.profiles_dir)
    profile_name = project_profile_name(project_dir)
    config = target_config(profile_name, profiles_file, args.target)
    schema = args.schema

    parquet_files = sorted(data_dir.glob("*.parquet"))
    if not parquet_files:
        raise SystemExit(f"Nenhum parquet encontrado em {data_dir}")

    duck_connection = duckdb.connect()
    pg_connection = postgres_connection(config)
    try:
        for path in parquet_files:
            load_parquet(
                duck_connection,
                pg_connection,
                schema,
                path,
                args.batch_size,
                args.if_exists,
            )
    finally:
        duck_connection.close()
        pg_connection.close()


if __name__ == "__main__":
    main()

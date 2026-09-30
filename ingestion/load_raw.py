"""Carrega os CSVs brutos do Olist para dentro do DuckDB na camada raw.

Dataset: https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
Baixe os 9 CSVs e coloque em data/raw/ (o geolocation é opcional).

Para trabalhar com uma amostra menor, ajuste SAMPLE_FRACTION abaixo
(ex: 0.1 usa 10% dos pedidos — mantém coerência entre as tabelas).
"""
import os
import duckdb

DB_PATH = "data/olist.duckdb"
RAW_DIR = "data/raw"

# 1.0 = dataset completo | 0.1 = 10% | 0.05 = 5%
SAMPLE_FRACTION = 1.0

TABELAS = [
    "olist_orders_dataset",
    "olist_customers_dataset",
    "olist_order_items_dataset",
    "olist_products_dataset",
    "olist_sellers_dataset",
    "olist_order_payments_dataset",
    "olist_order_reviews_dataset",
    "product_category_name_translation",
]


def main():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"Banco antigo removido: {DB_PATH}")

    con = duckdb.connect(DB_PATH)
    con.execute("CREATE SCHEMA IF NOT EXISTS raw;")

    for tabela in TABELAS:
        caminho = f"{RAW_DIR}/{tabela}.csv"
        if not os.path.exists(caminho):
            print(f"!! pulando {tabela} (arquivo não encontrado)")
            continue

        con.execute(f"""
            CREATE OR REPLACE TABLE raw.{tabela} AS
            SELECT * FROM read_csv_auto('{caminho}', header=true)
        """)

        if tabela == "olist_orders_dataset" and SAMPLE_FRACTION < 1.0:
            # Amostragem coerente: escolhe pedidos e filtra as tabelas filhas por eles
            con.execute(f"""
                CREATE OR REPLACE TABLE raw.amostra_pedidos AS
                SELECT order_id FROM raw.olist_orders_dataset
                USING SAMPLE {SAMPLE_FRACTION}
            """)
            con.execute("""
                DELETE FROM raw.olist_orders_dataset
                WHERE order_id NOT IN (SELECT order_id FROM raw.amostra_pedidos)
            """)
            for filha, col in [
                ("olist_order_items_dataset", "order_id"),
                ("olist_order_payments_dataset", "order_id"),
                ("olist_order_reviews_dataset", "order_id"),
            ]:
                con.execute(f"""
                    DELETE FROM raw.{filha}
                    WHERE {col} NOT IN (SELECT order_id FROM raw.amostra_pedidos)
                """)

        count = con.execute(f"SELECT COUNT(*) FROM raw.{tabela}").fetchone()[0]
        print(f"✓ raw.{tabela}: {count:,} linhas")

    con.close()
    print("Ingestão concluída.")


if __name__ == "__main__":
    main()

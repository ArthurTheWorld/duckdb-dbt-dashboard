# Pipeline DuckDB + dbt + Streamlit — Olist E-commerce

Pipeline analítico de ponta a ponta sobre o **dataset Olist**, o maior dataset
público de e-commerce brasileiro: ~100 mil pedidos de um marketplace real
entre 2016 e 2018, com 9 tabelas relacionadas.

**Arquitetura:**

```
CSVs (data/raw/, baixados do Kaggle)
      │  ingestion/load_raw.py
      ▼
raw.*                                   (8 tabelas no DuckDB)
      │  dbt (models/staging/)
      ▼
staging.stg_*                           (7 views: limpeza e padronização)
      │  dbt (models/marts/)
      ▼
marts.fct_order_items                   (tabela fato: item de pedido)
marts.dim_customers / dim_products / dim_sellers
marts.agg_sales_monthly / agg_sales_by_state / agg_category_sales / agg_payments
      │  app.py (Streamlit)
      ▼
Dashboard interativo (KPIs, filtros, gráficos Plotly, explorador de tabelas)
```

## Stack

| Camada | Tecnologia |
|---|---|
| Linguagem | Python 3.11+ |
| Banco analítico | DuckDB (OLAP embarcado, zero infraestrutura) |
| Transformação | dbt + dbt-duckdb |
| Ingestão | Python + pandas |
| Dashboard | Streamlit |
| Visualização | Plotly |
| Fonte de dados | Kaggle (dataset Olist) |
| Versionamento | Git + GitHub |

## Dataset

[Olist — Brazilian E-Commerce Public Dataset](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce),
publicado pela Olist e disponível no Kaggle. Os CSVs (~120 MB) **não estão
neste repositório** — faça o download e coloque-os em `data/raw/`
(veja `data/raw/LEIA-ME.txt` para a lista de arquivos).

Se quiser trabalhar com menos dados, ajuste `SAMPLE_FRACTION` em
`ingestion/load_raw.py` (ex: `0.1` usa 10% dos pedidos, mantendo coerência
entre pedidos, itens, pagamentos e avaliações).

## Como rodar

```bash
pip install -r requirements.txt

# 1. coloque os CSVs em data/raw/ e carregue no DuckDB
python ingestion/load_raw.py

# 2. transformações + testes de qualidade
cd dbt_project && dbt run && dbt test && cd ..

# 3. dashboard
streamlit run app.py
```

## Decisões técnicas

- **Staging como `view`, marts como `table`**: staging é barato de recalcular;
  marts são agregações consumidas pelo dashboard, então vão materializados.
- **Fato no nível do item de pedido** (`fct_order_items`): um pedido tem vários
  itens com preços e fretes distintos — granularidade certa evita somas duplicadas.
- **Amostragem coerente**: ao reduzir o dataset, os pedidos amostrados filtram
  as tabelas filhas (itens, pagamentos, avaliações), mantendo integridade referencial.
- **`category` traduzida na staging**: o join com `product_category_name_translation`
  acontece uma única vez, antes dos marts.
- **`delivery_days` calculado na fato**: dias entre compra e entrega, pronto
  para análise de prazo no dashboard.
- **Testes dbt** (`dbt test`): `unique`/`not_null` nas chaves das dims e
  `relationships` entre fato e dimensão de clientes.

## Dashboard (Streamlit)

- **Filtros**: período, estado do cliente (UF), categoria de produto
- **KPIs**: GMV, pedidos, ticket médio, frete médio, nota média de avaliação
- **Aba Vendas**: receita e pedidos mensais, receita por UF, ticket × volume por estado
- **Aba Produtos**: top categorias por receita, preço × nota, dimensão de produtos
- **Aba Pagamentos & Entrega**: métodos de pagamento, parcelamento, prazo de
  entrega, distribuição das notas
- **Aba Explorar dados**: qualquer tabela do banco (raw, staging ou marts)

O app conecta em modo somente leitura (`read_only=True`), usa cache
(`st.cache_data`, TTL 60s) e trata banco ausente ou marts não materializados
com instruções de como rodar o pipeline.

## Estrutura do repositório

```
duckdb-dbt-project/
├── data/raw/                       # CSVs do Olist (não versionados)
├── ingestion/load_raw.py           # CSVs -> schema raw no DuckDB
├── dbt_project/
│   ├── models/staging/             # 7 views de limpeza e padronização
│   ├── models/marts/               # Fato, 3 dimensões e 4 agregações
│   ├── dbt_project.yml
│   └── profiles.yml
├── app.py                          # Dashboard Streamlit
├── requirements.txt
└── README.md
```

## Testes de qualidade

```bash
cd dbt_project
dbt test
```

Cobrem:

- `unique` e `not_null` nas chaves primárias das dimensões
- `relationships` entre `fct_order_items` e `dim_customers`
- `accepted_values` em campos categóricos (ex: status de pedido)

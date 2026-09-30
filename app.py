"""
Dashboard Streamlit — Olist E-commerce (DuckDB + dbt)

Como rodar:
    1. Baixe o dataset em
       https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce
       e coloque os CSVs em data/raw/
    2. python ingestion/load_raw.py
    3. cd dbt_project && dbt run && dbt test && cd ..
    4. streamlit run app.py
"""
import os
import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st

DB_PATH = "data/olist.duckdb"

st.set_page_config(page_title="Olist — Dashboard E-commerce", page_icon="🇧🇷", layout="wide")


# ---------------------------------------------------------------- conexão
@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


@st.cache_data(ttl=60, show_spinner="Consultando DuckDB...")
def run_query(sql: str) -> pd.DataFrame:
    return get_connection().execute(sql).df()


# ---------------------------------------------------------------- checagem
if not os.path.exists(DB_PATH):
    st.error(
        "Banco não encontrado em `data/olist.duckdb`. Rode o pipeline:\n\n"
        "`python ingestion/load_raw.py`\n"
        "`cd dbt_project && dbt run`"
    )
    st.stop()

tabelas = run_query(
    "SELECT table_schema, table_name FROM information_schema.tables "
    "WHERE table_schema NOT IN ('information_schema','pg_catalog') ORDER BY 1, 2"
)
tem_marts = {"marts.fct_order_items"}.issubset(
    set(tabelas["table_schema"] + "." + tabelas["table_name"])
)
if not tem_marts:
    st.warning("Marts não encontrados. Rode `dbt run` dentro de `dbt_project/`.")
    st.stop()

# ---------------------------------------------------------------- sidebar
st.sidebar.title("🇧🇷 Olist E-commerce")
st.sidebar.caption("~100 mil pedidos de um marketplace brasileiro (2016–2018)")

df_fct = run_query("SELECT * FROM marts.fct_order_items")
df_fct["purchase_date"] = pd.to_datetime(df_fct["purchase_date"])

min_d = df_fct["purchase_date"].min().date()
max_d = df_fct["purchase_date"].max().date()
faixa = st.sidebar.date_input("Período", value=(min_d, max_d), min_value=min_d, max_value=max_d)

ufs = sorted(df_fct["customer_state"].dropna().unique())
ufs_sel = st.sidebar.multiselect("Estado do cliente (UF)", options=ufs, default=ufs)

cats = ["(todas)"] + sorted(df_fct["category"].dropna().unique())
cat_sel = st.sidebar.selectbox("Categoria de produto", options=cats)

st.sidebar.markdown("---")
st.sidebar.caption(f"Banco: `{DB_PATH}`")
if st.sidebar.button("🔄 Recarregar dados"):
    st.cache_data.clear()
    st.rerun()

# ---------------------------------------------------------------- filtros
mask = df_fct["customer_state"].isin(ufs_sel)
if isinstance(faixa, tuple) and len(faixa) == 2:
    mask &= df_fct["purchase_date"].dt.date.between(faixa[0], faixa[1])
if cat_sel != "(todas)":
    mask &= df_fct["category"] == cat_sel
f = df_fct[mask]

# ---------------------------------------------------------------- header
st.title("Dashboard — Olist E-commerce")
st.caption("Camadas: `raw` (9 CSVs) → `staging` (views dbt) → `marts` (tabela fato + dims + agregações)")

# ---------------------------------------------------------------- KPIs
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("💰 Receita (GMV)", f"R$ {f['total_value'].sum():,.2f}")
c2.metric("🛒 Pedidos", f"{f['order_id'].nunique():,}")
c3.metric("🎫 Ticket médio", f"R$ {f['total_value'].mean():,.2f}" if len(f) else "—")
c4.metric("🚚 Frete médio", f"R$ {f['freight_value'].mean():,.2f}" if len(f) else "—")
c5.metric("⭐ Nota média", f"{f['review_score'].mean():.1f}" if f['review_score'].notna().any() else "—")

st.markdown("---")

aba1, aba2, aba3, aba4 = st.tabs(["📈 Vendas", "📦 Produtos", "💳 Pagamentos & Entrega", "🗃️ Explorar dados"])

# ---- Vendas
with aba1:
    monthly = run_query("SELECT * FROM marts.agg_sales_monthly")
    monthly["month"] = pd.to_datetime(monthly["month"])
    if isinstance(faixa, tuple) and len(faixa) == 2:
        monthly = monthly[monthly["month"].dt.date.between(faixa[0], faixa[1])]

    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.line(monthly, x="month", y="revenue", markers=True,
                title="Receita mensal (pedidos entregues)",
                labels={"month": "Mês", "revenue": "Receita (R$)"}),
        use_container_width=True)
    col2.plotly_chart(
        px.bar(monthly, x="month", y="orders",
               title="Pedidos por mês", labels={"month": "Mês", "orders": "Pedidos"}),
        use_container_width=True)

    by_state = run_query("SELECT * FROM marts.agg_sales_by_state")
    if ufs_sel:
        by_state = by_state[by_state["customer_state"].isin(ufs_sel)]
    col1.plotly_chart(
        px.bar(by_state, x="customer_state", y="revenue", color="avg_review_score",
               title="Receita por estado (UF)",
               labels={"customer_state": "UF", "revenue": "Receita (R$)", "avg_review_score": "Nota média"}),
        use_container_width=True)
    col2.plotly_chart(
        px.scatter(by_state, x="orders", y="avg_ticket", size="revenue", text="customer_state",
                   title="Ticket médio × nº de pedidos por estado",
                   labels={"orders": "Pedidos", "avg_ticket": "Ticket médio (R$)", "customer_state": "UF"}),
        use_container_width=True)

# ---- Produtos
with aba2:
    cat = run_query("SELECT * FROM marts.agg_category_sales")
    if cat_sel != "(todas)":
        cat = cat[cat["category"] == cat_sel]
    top_n = st.slider("Top N categorias", 5, 30, 15)
    cat_top = cat.head(top_n)

    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.bar(cat_top, x="revenue", y="category", orientation="h",
               title=f"Top {top_n} categorias por receita",
               labels={"category": "Categoria", "revenue": "Receita (R$)"}),
        use_container_width=True)
    col2.plotly_chart(
        px.scatter(cat_top, x="avg_price", y="avg_review_score", size="orders",
                   color="category", title="Preço médio × nota média por categoria",
                   labels={"avg_price": "Preço médio (R$)", "avg_review_score": "Nota média"}),
        use_container_width=True)

    st.subheader("Dimensão de produtos (marts.dim_products)")
    dim_p = run_query("SELECT * FROM marts.dim_products ORDER BY total_revenue DESC")
    st.dataframe(dim_p.head(100).style.format({"total_revenue": "R$ {:,.2f}", "avg_review_score": "{:.1f}"}),
                 use_container_width=True, hide_index=True)

# ---- Pagamentos & Entrega
with aba3:
    pay = run_query("SELECT * FROM marts.agg_payments")
    col1, col2 = st.columns(2)
    col1.plotly_chart(
        px.pie(pay, names="payment_type", values="total_value", hole=0.4,
               title="Receita por método de pagamento"),
        use_container_width=True)
    col2.plotly_chart(
        px.bar(pay, x="payment_type", y="avg_installments",
               title="Parcelamento médio por método",
               labels={"payment_type": "Método", "avg_installments": "Parcelas médias"}),
        use_container_width=True)

    ent = f[f["delivery_days"].notna() & (f["order_status"] == "delivered")]
    col1.plotly_chart(
        px.histogram(ent, x="delivery_days", nbins=60,
                     title="Distribuição do prazo de entrega (dias)",
                     labels={"delivery_days": "Dias até a entrega"}),
        use_container_width=True)
    col2.plotly_chart(
        px.histogram(f[f["review_score"].notna()], x="review_score", nbins=5,
                     title="Distribuição das notas de avaliação",
                     labels={"review_score": "Nota (1–5)"}),
        use_container_width=True)

# ---- Explorar dados
with aba4:
    escolha = st.selectbox("Tabela", options=(tabelas["table_schema"] + "." + tabelas["table_name"]).tolist())
    df_raw = run_query(f"SELECT * FROM {escolha} LIMIT 5000")
    st.caption(f"Mostrando até 5.000 linhas — {len(df_raw):,} linhas × {len(df_raw.columns)} colunas")
    st.dataframe(df_raw, use_container_width=True, hide_index=True)

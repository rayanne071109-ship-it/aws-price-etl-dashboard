import streamlit as st
import pandas as pd

@st.cache_data
def load_data():
    return pd.read_parquet("../data/produtos.parquet")

df = load_data()

# Regiões comerciais "padrão", ativas por padrão em qualquer conta AWS
REGIOES_PADRAO = [
    "us-east-1", "us-east-2", "us-west-1", "us-west-2",
    "eu-west-1", "eu-west-2", "eu-west-3", "eu-central-1", "eu-north-1",
    "ap-southeast-1", "ap-southeast-2", "ap-northeast-1", "ap-northeast-2", "ap-northeast-3",
    "ap-south-1", "sa-east-1", "ca-central-1",
]

df = df[df["region_code"].isin(REGIOES_PADRAO)]

st.title("Dashboard AWS Prices")

# Filtro por região
regiao = st.selectbox("Selecione a região:", df["region_code"].unique())
df_filtrado = df[df["region_code"] == regiao]

# Ordenação por preço
ordem = st.radio(
    "Ordenar por preço:",
    ["Menor para maior", "Maior para menor"],
    horizontal=True,
)
ascending = ordem == "Menor para maior"
df_filtrado = df_filtrado.sort_values("price_per_hour_usd", ascending=ascending)

# Mostrar tabela
st.subheader("Tabela de instâncias filtradas")
st.dataframe(
    df_filtrado[[
        "instance_type",
        "instance_family",
        "vcpu",
        "memory_gib",
        "operating_system",
        "tenancy",
        "price_per_hour_usd",
    ]].head(50),
    use_container_width=True,
    hide_index=True,
    column_config={
        "price_per_hour_usd": st.column_config.NumberColumn(
            "Preço/hora (USD)",
            format="$%.4f",
        ),
        "memory_gib": st.column_config.NumberColumn(
            "Memória (GiB)",
            format="%.1f",
        ),
        "instance_type": "Tipo de instância",
        "instance_family": "Família",
        "vcpu": "vCPU",
        "operating_system": "SO",
        "tenancy": "Tenancy",
    },
)

# Gráfico memória vs vCPU
st.subheader("Memória vs vCPU")
st.scatter_chart(df_filtrado[["vcpu", "memory_gib"]])

# Gráfico de barras por família
st.subheader("Distribuição por família de instância")
st.bar_chart(df_filtrado["instance_family"].value_counts())

# Top 10 tipos de VM mais baratas (Linux, Shared, na região selecionada)
st.subheader("Top 10 tipos de VM mais baratas (Linux, Shared)")

top10 = (
    df_filtrado[
        (df_filtrado["operating_system"] == "Linux")
        & (df_filtrado["tenancy"] == "Shared")
    ]
    .sort_values("price_per_hour_usd", ascending=True)
    .drop_duplicates(subset="instance_type")  # evita repetir o mesmo tipo de VM
    .head(10)
)

st.bar_chart(top10.set_index("instance_type")["price_per_hour_usd"])

# Comparação entre regiões (preço médio)
st.subheader("Comparação de preço médio por região")

# usa o df completo (não o filtrado), pra comparar TODAS as regiões
preco_medio_regiao = (
    df.groupby("region_code")["price_per_hour_usd"]
    .mean()
    .sort_values()
    .reset_index()
)
preco_medio_regiao.columns = ["Região", "Preço médio/hora (USD)"]

st.bar_chart(preco_medio_regiao.set_index("Região"))


st.subheader("Comparação de preço por tipo de instância entre regiões")

tipo_escolhido = st.selectbox(
    "Escolha um tipo de instância pra comparar:",
    sorted(df["instance_type"].unique()),
)

df_tipo = df[
    (df["instance_type"] == tipo_escolhido)
    & (df["operating_system"] == "Linux")
    & (df["tenancy"] == "Shared")
].sort_values("price_per_hour_usd")

st.bar_chart(df_tipo.set_index("region_code")["price_per_hour_usd"])

col1, col2 = st.columns(2)
with col1:
    st.metric("Mais barata", df_tipo.iloc[0]["region_code"], f"${df_tipo.iloc[0]['price_per_hour_usd']:.4f}/h")
with col2:
    st.metric("Mais cara", df_tipo.iloc[-1]["region_code"], f"${df_tipo.iloc[-1]['price_per_hour_usd']:.4f}/h")
